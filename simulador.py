"""
Simulador de transmissão: fragmentação + EDC + enquadramento + camada física.

Reaproveita os módulos já existentes:
    enquadramento : contagem_de_caracteres.py  ("contagem")
                    insercaoBits.py            ("insercao")
    EDC           : checksum.py                ("checksum")
                    crc.py                     ("crc")
                    hamming.py                 ("hamming")
    banda base    : nrz_polar.py ("nrz_polar"), bipolar.py ("bipolar"),
                    manchester.py ("manchester")
    modulação     : ASK.py ("ASK"), FSK.py ("FSK"),
                    PSK_8.py ("8PSK"), QAM_32.py ("32QAM")
    canal         : AWGN.py (ruído gaussiano somado ao sinal)

Fluxo no transmissor, para cada fragmento da mensagem:
    payload -> (padding de zeros, se preciso) -> EDC -> enquadramento
            -> codificação banda base OU modulação -> + ruído AWGN

Fluxo no receptor (inverso):
    sinal ruidoso -> decodificação/demodulação -> desenquadramento -> EDC

Tamanhos de quadro em BITS.
"""

import contextlib
import io

import numpy as np
from CamadaFisica import *
from CamadaDeEnlace import *

ENQUADRAMENTOS = ("contagem", "insercao")
EDCS = ("checksum", "crc", "hamming")

CC_HEADER = 8                 # cabeçalho da contagem de caracteres (bits)
CC_MAX_BYTES = 255            # o cabeçalho de 8 bits só conta até 255 bytes
CRC_TAM = crc.R              # o CRC do crc.py é fixo em 32 bits

CODIFICACOES = ("nrz_polar", "bipolar", "manchester")   # banda base
MODULACOES = ("ASK", "FSK", "8PSK", "32QAM")            # passa-banda

# Parâmetros da camada física (podem ser sobrescritos via params_fisica=...)
PARAMS_FISICA = {
    "V": 1.0,                 # amplitude: VCC (NRZ), V (bipolar/Manchester/ASK), A (FSK)
                              # (8PSK e 32QAM têm amplitude fixa pela constelação)
    "amostras_por_bit": 100,  # Manchester e FSK (o ASK.py é fixo em 100)
    "f": 4,                   # ASK: ciclos da portadora por bit
    "f1": 8, "f2": 4,         # FSK: ciclos por bit para o '1' e para o '0'
    "fc": 4,                  # 8PSK / 32QAM: ciclos da portadora por símbolo
    "As": 400,                # 8PSK / 32QAM: amostras por símbolo
}


# --------------------------------------------------------------------------
# Auxiliares de dimensionamento
# --------------------------------------------------------------------------
def _orcamento_dados(tamQuadro, enquadramento):
    """Máximo de bits de (payload + EDC) que cabem em um quadro."""
    if enquadramento == "contagem":
        livre = min(tamQuadro - CC_HEADER, CC_MAX_BYTES * 8)
        return max((livre // 8) * 8, 0)          # a contagem é em bytes

    # inserção de bits: FLAG + dados com stuffing + FLAG.
    # Pior caso do stuffing: +1 bit a cada 5 uns seguidos (n + n//5).
    livre = tamQuadro - 2 * len(insercaoBits.FLAG)
    n = max(livre, 0)
    while n > 0 and n + n // 5 > livre:
        n -= 1
    return n


def _tam_dados(p, edc, tamEdc):
    """Tamanho de (payload + EDC) para um payload de p bits."""
    if edc == "checksum":
        return p + tamEdc
    if edc == "crc":
        return p + CRC_TAM
    return hamming.tamCodeWord(p)               # hamming: EDC embutido


def _valido(p, edc, tamEdc, enquadramento, orcamento):
    """Um payload de p bits é aceitável nesta configuração?"""
    d = _tam_dados(p, edc, tamEdc)
    if d > orcamento:
        return False
    if edc == "checksum" and p % tamEdc != 0:    # segmentos completos
        return False
    if enquadramento == "contagem" and d % 8 != 0:  # contagem é em bytes
        return False
    return True


def _aplicar_edc(payload, edc, tamEdc):
    """Devolve a string de bits payload+EDC (ou codeword, no Hamming)."""
    if edc == "checksum":
        return checksum.checksum_transmissor(tamEdc, payload)
    if edc == "crc":
        return payload + format(crc.crc_transmissor(payload), f"0{CRC_TAM}b")
    return "".join(hamming.hammingCode(payload))


def _enquadrar(dados, enquadramento):
    if enquadramento == "contagem":
        # dados é múltiplo de 8 e cabe em um quadro => gera exatamente 1 quadro
        return contagem_de_caracteres.cc_transmissor(len(dados) // 8, dados)
    return insercaoBits.build_frame(dados)


# --------------------------------------------------------------------------
# Camada física: codificação banda base / modulação / canal AWGN
# --------------------------------------------------------------------------
def _params(params_fisica):
    p = dict(PARAMS_FISICA)
    if params_fisica:
        desconhecidos = set(params_fisica) - set(PARAMS_FISICA)
        if desconhecidos:
            raise ValueError(f"params_fisica desconhecidos: {sorted(desconhecidos)}")
        p.update(params_fisica)
    return p


def _tem_fisica(codificacao, modulacao):
    """Valida a escolha (banda base OU modulação) e diz se há camada física."""
    if codificacao is not None and modulacao is not None:
        raise ValueError("escolha codificacao (banda base) OU modulacao, não as duas")
    if codificacao is not None and codificacao not in CODIFICACOES:
        raise ValueError(f"codificacao deve ser um de {CODIFICACOES}")
    if modulacao is not None and modulacao not in MODULACOES:
        raise ValueError(f"modulacao deve ser uma de {MODULACOES}")
    return codificacao is not None or modulacao is not None


def _fisica_tx(bits, codificacao, modulacao, p):
    """string de bits -> (sinal np.ndarray, n_pad). n_pad só existe em 8PSK/32QAM."""
    V, n_pad = p["V"], 0
    ints = [int(b) for b in bits]     # nrz/ASK/FSK comparam com inteiros (bit == 0/1)

    if codificacao == "nrz_polar":
        s = nrz_polar.codificar_nrz_polar(V, ints)
    elif codificacao == "bipolar":
        s = bipolar.codificadorBipolar(len(bits), bits, V)
    elif codificacao == "manchester":
        s = manchester.codificadorManchester(bits, V, p["amostras_por_bit"])
    elif modulacao == "ASK":
        if p["amostras_por_bit"] != 100:
            raise ValueError("o ASK.py usa 100 amostras por bit (valor fixo)")
        s = ASK.modulacaoASK(ints, p["f"], V)
    elif modulacao == "FSK":
        s = FSK.modulacaoFSK(V, p["f1"], p["f2"], ints, p["amostras_por_bit"])
    elif modulacao == "8PSK":
        n_pad, _, _, _, _, s = PSK_8.modulacao8PSK(bits, p["fc"], p["As"])
    else:  # 32QAM
        n_pad, _, _, _, _, s = QAM_32.modulacao32QAM(bits, p["fc"], p["As"])
    return np.asarray(s, dtype=float), n_pad


def _fisica_rx(sinal, n_pad, codificacao, modulacao, p):
    """sinal ruidoso -> string de bits do quadro."""
    V = p["V"]

    if codificacao == "nrz_polar":
        # decodificar_nrz_polar compara com ==, o que nunca vale com ruído.
        # Por isso um decisor por limiar (0 V) recoloca cada amostra em ±V antes.
        decidido = [V if x >= 0 else -V for x in sinal]
        bits = nrz_polar.decodificar_nrz_polar(V, decidido)
    elif codificacao == "bipolar":
        bits = bipolar.decodificadorBipolar(sinal, V)
    elif codificacao == "manchester":
        bits = manchester.decodificadorManchester(sinal, V, p["amostras_por_bit"])
    elif modulacao == "ASK":
        bits = ASK.demodulacaoASK(sinal, V, p["f"], 100)
    elif modulacao == "FSK":
        bits = FSK.demodulacaoFSK(sinal, V, p["f1"], p["f2"], p["amostras_por_bit"])
    elif modulacao == "8PSK":
        x_hat, y_hat = PSK_8.demodulate(sinal, p["fc"], p["As"])
        return PSK_8.parallel_to_serial(PSK_8.decide(x_hat, y_hat), n_pad)
    else:  # 32QAM
        x_hat, y_hat = QAM_32.demodulate(sinal, p["fc"], p["As"])
        return QAM_32.parallel_to_serial(QAM_32.decide(x_hat, y_hat), n_pad)
    return "".join(str(b) for b in bits)


# --------------------------------------------------------------------------
# Transmissão
# --------------------------------------------------------------------------
def simular_transmissao(mensagem, tamQuadro, tamEdc, enquadramento, edc,
                        codificacao=None, modulacao=None, sigma=0.0,
                        semente=None, params_fisica=None, verbose=False):
    """
    Gera os quadros e, opcionalmente, os transmite pela camada física.

    mensagem      : string (ou lista) de bits, ex.: "0110101..."
    tamQuadro     : tamanho MÁXIMO do quadro final, em bits
                    (já contando cabeçalho/flags e o stuffing)
    tamEdc        : tamanho do EDC em bits
                      - "checksum": tamanho do segmento (= tamanho do checksum)
                      - "crc"     : fixo em 32 (limitado pelo crc.py)
                      - "hamming" : ignorado (depende do tamanho do payload)
    enquadramento : "contagem" | "insercao"
    edc           : "checksum" | "crc" | "hamming"

    Camada física (opcional; escolha UMA das duas):
    codificacao   : banda base  -> "nrz_polar" | "bipolar" | "manchester"
    modulacao     : passa-banda -> "ASK" | "FSK" | "8PSK" | "32QAM"
    sigma         : desvio padrão do ruído AWGN, na mesma unidade da amplitude
                    (0 = canal sem ruído)
    semente       : semente do ruído (None = aleatório). Cada quadro usa
                    semente + índice, para o ruído não se repetir entre quadros.
    params_fisica : dict para sobrescrever PARAMS_FISICA (V, f, f1, f2, ...)
    verbose       : imprime um resumo de cada quadro

    Retorno:
      - sem camada física: lista de strings de bits, um item por quadro;
      - com camada física: lista de dicts, um por quadro:
            "sinal_tx": sinal gerado pelo transmissor (sem ruído)
            "sinal_rx": sinal que chega ao receptor (sinal_tx + AWGN)
            "n_pad"   : bits de padding do modulador (8PSK/32QAM; senão 0)
        Esta lista pode ser passada direto para simular_recepcao.
    """
    fisica = _tem_fisica(codificacao, modulacao)
    if sigma < 0:
        raise ValueError("sigma deve ser >= 0")
    if sigma > 0 and not fisica:
        raise ValueError("sigma só tem efeito com codificacao ou modulacao")
    p = _params(params_fisica)

    mensagem = "".join(str(x) for x in mensagem)
    if not mensagem or set(mensagem) - {"0", "1"}:
        raise ValueError("a mensagem deve ser uma string não vazia de 0s e 1s")
    if enquadramento not in ENQUADRAMENTOS:
        raise ValueError(f"enquadramento deve ser um de {ENQUADRAMENTOS}")
    if edc not in EDCS:
        raise ValueError(f"edc deve ser um de {EDCS}")

    if edc == "checksum":
        if not isinstance(tamEdc, int) or tamEdc < 1:
            raise ValueError("para checksum, tamEdc deve ser um inteiro >= 1")
    elif edc == "crc" and tamEdc not in (None, CRC_TAM):
        raise ValueError(f"o CRC do crc.py é fixo em {CRC_TAM} bits")

    # Quantos bits de payload cabem por quadro?
    orcamento = _orcamento_dados(tamQuadro, enquadramento)
    p_max = next((q for q in range(orcamento, 0, -1)
                  if _valido(q, edc, tamEdc, enquadramento, orcamento)), 0)
    if p_max == 0:
        raise ValueError(
            f"tamQuadro={tamQuadro} é pequeno demais para {enquadramento} + {edc}"
        )

    quadros, saida = [], []
    for inicio in range(0, len(mensagem), p_max):
        fragmento = mensagem[inicio:inicio + p_max]

        # Menor payload >= fragmento que satisfaz o alinhamento (padding de 0s)
        q = next(x for x in range(len(fragmento), p_max + 1)
                 if _valido(x, edc, tamEdc, enquadramento, orcamento))
        padding = q - len(fragmento)
        payload = fragmento + "0" * padding

        dados = _aplicar_edc(payload, edc, tamEdc)
        quadro = _enquadrar(dados, enquadramento)
        assert len(quadro) <= tamQuadro, "quadro excedeu tamQuadro"
        quadros.append(quadro)
        idx = len(quadros) - 1

        if fisica:
            sinal_tx, n_pad = _fisica_tx(quadro, codificacao, modulacao, p)
            if sigma > 0:    # o meio soma o ruído AWGN ao sinal
                sinal_rx = AWGN.canalAwgn(sinal_tx, 0.0, sigma,
                                           None if semente is None else semente + idx)
            else:
                sinal_rx = sinal_tx.copy()
            saida.append({"sinal_tx": sinal_tx, "sinal_rx": sinal_rx, "n_pad": n_pad})

        if verbose:
            print(f"[{idx}] payload={len(fragmento)}b padding={padding}b "
                  f"edc={len(dados) - q}b quadro={len(quadro)}/{tamQuadro}b")
            print(f"    {quadro}")
            if fisica:
                nome = codificacao or modulacao
                print(f"    {nome}: {len(sinal_tx)} amostras, n_pad={n_pad}, "
                      f"sigma={sigma}")

    return saida if fisica else quadros


# --------------------------------------------------------------------------
# Recepção
# --------------------------------------------------------------------------
def _desenquadrar(quadro, enquadramento):
    """Devolve os bits de (payload + EDC) ou None se o enquadramento falhou."""
    if enquadramento == "contagem":
        r = contagem_de_caracteres.cc_receptor(quadro)
        return r[0] if isinstance(r, list) and len(r) == 1 else None
    r = insercaoBits.extract_frames(quadro)
    return r[0] if len(r) == 1 else None


def _verificar_edc(dados, tamEdc, edc):
    """Confere o EDC. Retorna (payload, ok, erro_pos)."""
    erro_pos = None
    if edc == "checksum":
        ok = checksum.checksum_receptor(tamEdc, dados) == "QUADRO SEM ERROS"
        payload = dados[:-tamEdc]
    elif edc == "crc":
        ok = crc.crc_receptor(dados)
        payload = dados[:-CRC_TAM]
    else:
        with contextlib.redirect_stdout(io.StringIO()):  # silencia os prints
            erro_pos = hamming.hammingCodeReceptor(list(dados))
        ok = erro_pos == 0
        cw = list(dados)
        if 0 < erro_pos <= len(cw):                      # corrige 1 bit
            cw[erro_pos - 1] = "1" if cw[erro_pos - 1] == "0" else "0"
        payload = "".join(b for i, b in enumerate(cw, start=1)
                          if i & (i - 1) != 0)
    return payload, ok, erro_pos


def simular_recepcao(quadros, tamEdc, enquadramento, edc,
                     codificacao=None, modulacao=None, params_fisica=None):
    """
    Processa cada quadro: demodula/decodifica (se houver camada física),
    desenquadra, confere o EDC e extrai o payload.

    quadros       : retorno de simular_transmissao (strings de bits, ou dicts
                    com "sinal_rx" quando há camada física)
    codificacao / modulacao / params_fisica: os MESMOS usados na transmissão.

    Retorna lista de dicts: {"payload", "ok", "erro_pos"}.
    - payload None significa que o quadro nem chegou a ser desenquadrado.
    - erro_pos só é preenchido no Hamming; nesse caso 1 bit errado é corrigido
      (ok fica False porque houve erro, mas o payload já vem corrigido).
    """
    fisica = _tem_fisica(codificacao, modulacao)
    p = _params(params_fisica)

    resultados = []
    for q in quadros:
        if fisica:
            if isinstance(q, dict):
                sinal, n_pad = q["sinal_rx"], q["n_pad"]
            else:
                sinal, n_pad = q, 0
            q = _fisica_rx(sinal, n_pad, codificacao, modulacao, p)
        elif isinstance(q, dict):
            raise ValueError("quadros com sinal exigem codificacao ou modulacao")

        dados = _desenquadrar(q, enquadramento)
        if dados is None:
            resultados.append({"payload": None, "ok": False, "erro_pos": None})
            continue
        try:
            payload, ok, erro_pos = _verificar_edc(dados, tamEdc, edc)
        except (ValueError, IndexError):   # quadro corrompido demais para o EDC
            payload, ok, erro_pos = None, False, None
        resultados.append({"payload": payload, "ok": ok, "erro_pos": erro_pos})
    return resultados


# --------------------------------------------------------------------------
# Auxiliares para mensagens de texto
# --------------------------------------------------------------------------
def texto_para_bits(texto):
    """Texto -> string de bits (UTF-8, 8 bits por byte)."""
    return "".join(format(b, "08b") for b in texto.encode("utf-8"))


def bits_para_texto(bits):
    """String de bits -> texto (descarta bits que não completam um byte)."""
    bits = bits[:len(bits) // 8 * 8]
    dados = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    return dados.decode("utf-8", errors="replace")


def montar_mensagem(resultados, n_bits):
    """Concatena os payloads recebidos e remove o padding final.
    Quadros que não puderam ser desenquadrados (payload None) são pulados."""
    bits = "".join(r["payload"] for r in resultados if r["payload"] is not None)
    return bits[:n_bits]