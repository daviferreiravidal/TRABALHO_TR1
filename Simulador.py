"""
Simulador de redes simples: camada de enlace + camada física + canal AWGN.

Rotina principal: chama as funções de CamadaEnlace.py e CamadaFisica.py
para simular a transmissão, e abre a interface gráfica (InterfaceGUI.py).

    python Simulador.py          abre a interface gráfica

Transmissor:
    texto -> bits -> fatias de N bits (completa com 0s)
          -> EDC -> enquadramento               (um quadro por fatia)
          -> fluxo de bits (todos os quadros em sequência)
          -> CODIFICAÇÃO de banda base           (NRZ polar | Manchester | Bipolar)
          -> MODULAÇÃO por portadora             (Nenhuma | ASK | FSK | 8-PSK | 32-QAM)
          -> canal AWGN

Receptor (caminho inverso):
    sinal -> demodulação -> sinal codificado recuperado -> decodificação
          -> fluxo de bits -> desenquadramento -> EDC -> bits -> texto

Convenção usada em todo o projeto: bits são SEMPRE strings, ex.: "0110".
"""

import sys
from dataclasses import dataclass

import numpy as np

import CamadaEnlace
import CamadaFisica


# --------------------------------------------------------------------------
# Configuração (o que o usuário escolhe na interface)
# --------------------------------------------------------------------------
@dataclass
class Config:
    enquadramento: str = "Inserção de bits"
    edc: str = "CRC-32"
    codificacao: str = "NRZ polar"
    modulacao: str = "ASK"
    bytes_por_quadro: int = 4     # tamanho da carga útil de cada quadro
    sigma: float = 0.0            # desvio padrão do ruído AWGN
    V: float = 1.0                # amplitude do sinal
    semente: int | None = None    # semente do ruído (None = aleatório)


# Limites aceitos (a GUI usa os mesmos valores)
MAX_BYTES_MENSAGEM = 2048
MAX_BYTES_QUADRO = 32
MAX_SIGMA = 10.0


def validar(texto, cfg):
    """Levanta ValueError com uma mensagem legível se algo estiver fora do lugar."""
    if not texto:
        raise ValueError("a mensagem está vazia")
    n = len(texto.encode("utf-8"))
    if n > MAX_BYTES_MENSAGEM:
        raise ValueError(f"mensagem com {n} bytes (máximo {MAX_BYTES_MENSAGEM})")
    for nome, tabela, valor in (("enquadramento", ENQUADRAMENTOS, cfg.enquadramento),
                                ("EDC", EDCS, cfg.edc),
                                ("codificação", CODIFICACOES, cfg.codificacao),
                                ("modulação", MODULACOES, cfg.modulacao)):
        if valor not in tabela:
            raise ValueError(f"{nome} desconhecido: {valor!r}")
    if not 1 <= cfg.bytes_por_quadro <= MAX_BYTES_QUADRO:
        raise ValueError(f"bytes por quadro deve estar entre 1 e {MAX_BYTES_QUADRO}")
    if not 0 <= cfg.sigma <= MAX_SIGMA:
        raise ValueError(f"σ deve estar entre 0 e {MAX_SIGMA}")
    if cfg.V <= 0:
        raise ValueError("a amplitude V deve ser positiva")


# Parâmetros fixos da camada física (simples de propósito)
AMOSTRAS_POR_CHIP = 100    # banda base, ASK e FSK: amostras por chip do sinal codificado
F_ASK = 4                  # ASK: ciclos da portadora por chip
F_MIN_FSK, F_MAX_FSK = 4, 8  # FSK: faixa de frequências (ciclos por chip)
FC = 4                     # 8-PSK / 32-QAM: ciclos por símbolo
AMOSTRAS_POR_SIMBOLO = 400 # 8-PSK / 32-QAM
SEGMENTO_CHECKSUM = 8      # bits


# --------------------------------------------------------------------------
# Tabelas: cada técnica é um par (transmissor, receptor)
# Para adicionar uma técnica nova, basta acrescentar uma linha.
# --------------------------------------------------------------------------

# EDC: tx(payload) -> dados ;  rx(dados) -> (payload, ok, posicao_corrigida)
#      tam(n) -> tamanho de "dados" para um payload de n bits
def _hamming_rx(dados):
    payload, pos = CamadaEnlace.hammingDecodifica(dados)
    return payload, pos == 0, pos

EDCS = {
    "Nenhum": (
        lambda b: b,
        lambda d: (d, True, 0),
        lambda n: n),
    "Paridade par": (
        lambda b: CamadaEnlace.adicionarBitParidade(b, "par"),
        lambda d: (lambda ok, dados: (dados, ok, 0))(*CamadaEnlace.verificarBitParidade(d, "par")),
        lambda n: n + 1),
    "Checksum": (
        lambda b: CamadaEnlace.checksum_transmissor(SEGMENTO_CHECKSUM, b),
        lambda d: (d[:-SEGMENTO_CHECKSUM], CamadaEnlace.checksum_receptor(SEGMENTO_CHECKSUM, d), 0),
        lambda n: n + SEGMENTO_CHECKSUM),
    "CRC-32": (
        lambda b: b + format(CamadaEnlace.crc_transmissor(b), "032b"),
        lambda d: (d[:-CamadaEnlace.R], CamadaEnlace.crc_receptor(d), 0),
        lambda n: n + CamadaEnlace.R),
    "Hamming": (
        CamadaEnlace.hammingCode,
        _hamming_rx,
        CamadaEnlace.tamCodeWord),
}

# Enquadramento: tx(dados) -> quadro
#                rx(fluxo, tam) -> lista com o conteúdo de cada quadro encontrado
#                (tam = bits de payload+EDC esperados; só o entrelaçamento,
#                 que usa quadros de tamanho fixo, precisa dele)
def _completa_byte(dados):
    return dados + "0" * (-len(dados) % 8)      # enquadramentos orientados a byte

def _contagem_tx(dados):
    dados = _completa_byte(dados)
    return CamadaEnlace.cc_transmissor(len(dados) // 8, dados)

ENQUADRAMENTOS = {
    "Contagem de caracteres": (_contagem_tx,
                               lambda f, tam: CamadaEnlace.cc_receptor(f)),
    "Inserção de bytes": (lambda d: CamadaEnlace.build_frame_bytes(_completa_byte(d)),
                          lambda f, tam: CamadaEnlace.extract_frames_bytes(f)),
    "Inserção de bits": (CamadaEnlace.build_frame_bits,
                         lambda f, tam: CamadaEnlace.extract_frames_bits(f)),
    "Entrelaçamento": (CamadaEnlace.build_frame_entrelacamento, CamadaEnlace.extract_frames_entrelacamento),
}

# Codificação de banda base:
#   cod(bits, V) -> sinal codificado (um nível por chip: -V, 0 ou +V)
#   dec(sinal codificado, V) -> bits
#   niveis: níveis possíveis do código (o modulador precisa saber)
CODIFICACOES = {
    "NRZ polar": (
        lambda b, V: CamadaFisica.codificadorNRZPolar(b, V),
        lambda s, V: CamadaFisica.decodificadorNRZPolar(s, V),
        CamadaFisica.NIVEIS_NRZ_POLAR),
    "Manchester": (
        lambda b, V: CamadaFisica.codificadorManchester(b, V, CamadaFisica.CHIPS_POR_BIT_MANCHESTER),
        lambda s, V: CamadaFisica.decodificadorManchester(s, V, CamadaFisica.CHIPS_POR_BIT_MANCHESTER),
        CamadaFisica.NIVEIS_MANCHESTER),
    "Bipolar": (
        lambda b, V: CamadaFisica.codificadorBipolar(len(b), b, V),
        lambda s, V: CamadaFisica.decodificadorBipolar(s, V),
        CamadaFisica.NIVEIS_BIPOLAR),
}

# Modulação por portadora (todas recebem o sinal JÁ codificado):
#   mod(sinal_codificado, V, niveis) -> (portadora, n_pad)
#   dem(portadora, V, niveis, n_pad) -> sinal codificado recuperado
def _banda_base_tx(sinal, V, niveis):
    """Sem portadora: cada chip vira AMOSTRAS_POR_CHIP amostras do mesmo nível."""
    return np.repeat(np.asarray(sinal, dtype=float), AMOSTRAS_POR_CHIP), 0

def _banda_base_rx(sinal, V, niveis, n_pad):
    """Integra (faz a média de) cada chip; o decodificador decide o bit."""
    n = len(sinal) // AMOSTRAS_POR_CHIP
    return list(np.asarray(sinal[:n * AMOSTRAS_POR_CHIP]).reshape(n, -1).mean(axis=1))

MODULACOES = {
    "Nenhuma (banda base)": (_banda_base_tx, _banda_base_rx),
    "ASK": (
        lambda s, V, nv: CamadaFisica.modulaASK(s, V, nv, F_ASK, AMOSTRAS_POR_CHIP),
        lambda p, V, nv, n: CamadaFisica.demodulaASK(p, V, nv, n, F_ASK, AMOSTRAS_POR_CHIP)),
    "FSK": (
        lambda s, V, nv: CamadaFisica.modulaFSK(s, V, nv, AMOSTRAS_POR_CHIP, F_MIN_FSK, F_MAX_FSK),
        lambda p, V, nv, n: CamadaFisica.demodulaFSK(p, V, nv, n, AMOSTRAS_POR_CHIP, F_MIN_FSK, F_MAX_FSK)),
    "8-PSK": (
        lambda s, V, nv: CamadaFisica.modula8PSK(s, V, nv, FC, AMOSTRAS_POR_SIMBOLO),
        lambda p, V, nv, n: CamadaFisica.demodula8PSK(p, V, nv, n, FC, AMOSTRAS_POR_SIMBOLO)),
    "32-QAM": (
        lambda s, V, nv: CamadaFisica.modula32QAM(s, V, nv, FC, AMOSTRAS_POR_SIMBOLO),
        lambda p, V, nv, n: CamadaFisica.demodula32QAM(p, V, nv, n, FC, AMOSTRAS_POR_SIMBOLO)),
}


# --------------------------------------------------------------------------
# Texto <-> bits
# --------------------------------------------------------------------------
def texto_para_bits(texto):
    return "".join(format(b, "08b") for b in texto.encode("utf-8"))


def bits_para_texto(bits):
    bits = bits[:len(bits) // 8 * 8]
    dados = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    return dados.decode("utf-8", errors="replace").rstrip("\x00")  # tira o padding


# --------------------------------------------------------------------------
# Transmissor, canal e receptor
# --------------------------------------------------------------------------
def transmitir(texto, cfg):
    """Devolve um dict com tudo que o transmissor produziu (para mostrar na GUI)."""
    validar(texto, cfg)
    edc_tx, _, _ = EDCS[cfg.edc]
    enq_tx, _ = ENQUADRAMENTOS[cfg.enquadramento]
    cod, _, niveis = CODIFICACOES[cfg.codificacao]
    mod, _ = MODULACOES[cfg.modulacao]

    bits = texto_para_bits(texto)
    n = 8 * cfg.bytes_por_quadro
    bits_pad = bits + "0" * (-len(bits) % n)          # último quadro completo com 0s

    quadros = []
    for i in range(0, len(bits_pad), n):
        payload = bits_pad[i:i + n]
        dados = edc_tx(payload)
        quadros.append({"payload": payload, "dados": dados, "quadro": enq_tx(dados)})

    fluxo = "".join(q["quadro"] for q in quadros)
    codificado = cod(fluxo, cfg.V)                     # 1º codifica (banda base)...
    sinal, n_pad = mod(codificado, cfg.V, niveis)      # ...depois modula a portadora
    return {"bits": bits, "quadros": quadros, "fluxo": fluxo,
            "codificado": np.asarray(codificado, dtype=float),
            "sinal": np.asarray(sinal, dtype=float), "n_pad": n_pad}


def canal(sinal, cfg, semente=None):
    """Meio de transmissão: soma ruído gaussiano branco (AWGN) ao sinal."""
    if cfg.sigma <= 0:
        return np.array(sinal, dtype=float)
    if semente is None:
        semente = cfg.semente
    return CamadaFisica.canalAwgn(sinal, 0.0, cfg.sigma, semente)


def receber(sinal, n_pad, cfg):
    """Devolve um dict com tudo que o receptor recuperou (para mostrar na GUI)."""
    _, edc_rx, edc_tam = EDCS[cfg.edc]
    _, enq_rx = ENQUADRAMENTOS[cfg.enquadramento]
    _, dec, niveis = CODIFICACOES[cfg.codificacao]
    _, dem = MODULACOES[cfg.modulacao]

    codificado = dem(sinal, cfg.V, niveis, n_pad)      # 1º demodula...
    fluxo = dec(codificado, cfg.V)                     # ...depois decodifica
    tam = edc_tam(8 * cfg.bytes_por_quadro)            # tamanho esperado de payload+EDC

    quadros = []
    for conteudo in enq_rx(fluxo, tam):
        dados = conteudo[:tam]                         # tira o padding de byte (contagem/bytes)
        if len(dados) < tam:
            quadros.append({"dados": dados, "payload": None, "status": "truncado"})
            continue
        try:
            payload, ok, pos = edc_rx(dados)
        except (ValueError, IndexError):           # quadro estragado demais para o EDC
            quadros.append({"dados": dados, "payload": None, "status": "erro"})
            continue
        status = "ok" if ok else ("corrigido" if pos else "erro")
        quadros.append({"dados": dados, "payload": payload, "status": status})

    # só entram na mensagem os quadros aceitos pelo EDC; os com erro são descartados
    bits = "".join(q["payload"] for q in quadros if q["status"] in ("ok", "corrigido"))
    return {"codificado": np.asarray(codificado, dtype=float), "fluxo": fluxo,
            "quadros": quadros, "bits": bits, "texto": bits_para_texto(bits)}


def estatisticas(tx, rx):
    """Números para o painel de estatísticas do receptor."""
    st = [q["status"] for q in rx["quadros"]]
    erros_canal = bits_errados(tx["fluxo"], rx["fluxo"])
    return {
        "bits_canal": len(tx["fluxo"]),
        "bits_errados": erros_canal,
        "ber": erros_canal / max(len(tx["fluxo"]), 1),
        "enviados": len(tx["quadros"]),
        "recebidos": len(st),
        "ok": st.count("ok"),
        "corrigidos": st.count("corrigido"),
        "erros": st.count("erro"),
        "truncados": st.count("truncado"),
        "perdidos": max(len(tx["quadros"]) - len(st), 0),
        "eficiencia": len(tx["bits"]) / max(len(tx["fluxo"]), 1),   # carga útil / bits no canal
        "mensagem_ok": rx["bits"][:len(tx["bits"])] == tx["bits"],
    }


def bits_errados(a, b):
    """Quantos bits diferem entre dois fluxos (diferença de tamanho conta como erro)."""
    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))


# --------------------------------------------------------------------------
# Rotina principal
# --------------------------------------------------------------------------
def main():
    """Abre a interface gráfica, entregando a ela este módulo (as tabelas de
    técnicas e as funções transmitir/canal/receber/estatisticas)."""
    import InterfaceGUI
    return InterfaceGUI.executar(sys.modules[__name__])


if __name__ == "__main__":
    sys.exit(main())
