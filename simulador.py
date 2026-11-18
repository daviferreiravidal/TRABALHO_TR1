"""
Simulador de redes simples: camada de enlace + camada física + canal AWGN.

Só a lógica (sem interface gráfica). A GUI está em gui.py.

Transmissor, para cada quadro:
    texto -> bits -> fatia de N bits (completa com 0s)
          -> EDC  -> enquadramento -> fluxo de bits
Depois, o fluxo inteiro passa pela camada física (banda base OU modulação)
e pelo canal AWGN.

Receptor (caminho inverso):
    sinal -> decodificação/demodulação -> fluxo de bits
          -> desenquadramento -> EDC -> bits -> texto

Convenção usada em todo o projeto: bits são SEMPRE strings, ex.: "0110".
"""

from dataclasses import dataclass

import numpy as np

from CamadaDeEnlace.Enquadramento import contagem_de_caracteres, insercaoBits
from CamadaDeEnlace.deteccaoErros import paridade, checksum, crc
from CamadaDeEnlace.correcaoErros import hamming
from CamadaFisica import AWGN
from CamadaFisica.codigosBandabase import nrz_polar, bipolar, manchester
from CamadaFisica.codigosBandaPassante import ASK, FSK, PSK_8, QAM_32


# --------------------------------------------------------------------------
# Configuração (o que o usuário escolhe na interface)
# --------------------------------------------------------------------------
@dataclass
class Config:
    enquadramento: str = "Inserção de bits"
    edc: str = "CRC-32"
    fisica: str = "NRZ polar"
    bytes_por_quadro: int = 4     # tamanho da carga útil de cada quadro
    sigma: float = 0.0            # desvio padrão do ruído AWGN
    V: float = 1.0                # amplitude do sinal


# Parâmetros fixos da camada física (simples de propósito)
AMOSTRAS_POR_BIT = 100     # Manchester, ASK, FSK
F_ASK = 4                  # ciclos da portadora por bit
F1_FSK, F2_FSK = 8, 4      # ciclos por bit para o '1' e para o '0'
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
    payload, pos = hamming.hammingDecodifica(dados)
    return payload, pos == 0, pos

EDCS = {
    "Nenhum": (
        lambda b: b,
        lambda d: (d, True, 0),
        lambda n: n),
    "Paridade par": (
        lambda b: paridade.adicionarBitParidade(b, "par"),
        lambda d: (lambda ok, dados: (dados, ok, 0))(*paridade.verificarBitParidade(d, "par")),
        lambda n: n + 1),
    "Checksum": (
        lambda b: checksum.checksum_transmissor(SEGMENTO_CHECKSUM, b),
        lambda d: (d[:-SEGMENTO_CHECKSUM], checksum.checksum_receptor(SEGMENTO_CHECKSUM, d), 0),
        lambda n: n + SEGMENTO_CHECKSUM),
    "CRC-32": (
        lambda b: b + format(crc.crc_transmissor(b), "032b"),
        lambda d: (d[:-crc.R], crc.crc_receptor(d), 0),
        lambda n: n + crc.R),
    "Hamming": (
        hamming.hammingCode,
        _hamming_rx,
        hamming.tamCodeWord),
}

# Enquadramento: tx(dados) -> quadro ;  rx(fluxo) -> lista de quadros (só o conteúdo)
def _contagem_tx(dados):
    dados = dados + "0" * (-len(dados) % 8)     # a contagem é em bytes
    return contagem_de_caracteres.cc_transmissor(len(dados) // 8, dados)

ENQUADRAMENTOS = {
    "Contagem de caracteres": (_contagem_tx, contagem_de_caracteres.cc_receptor),
    "Inserção de bits": (insercaoBits.build_frame, insercaoBits.extract_frames),
}

# Camada física: tx(bits, V) -> (sinal, n_pad) ;  rx(sinal, V, n_pad) -> bits
def _psk_tx(bits, V):
    n_pad, *_, S = PSK_8.modulacao8PSK(bits, FC, AMOSTRAS_POR_SIMBOLO)
    return V * S, n_pad

def _psk_rx(sinal, V, n_pad):
    x, y = PSK_8.demodulate(np.asarray(sinal) / V, FC, AMOSTRAS_POR_SIMBOLO)
    return PSK_8.parallel_to_serial(PSK_8.decide(x, y), n_pad)

def _qam_tx(bits, V):
    n_pad, *_, S = QAM_32.modulacao32QAM(bits, FC, AMOSTRAS_POR_SIMBOLO)
    return V * S, n_pad

def _qam_rx(sinal, V, n_pad):
    x, y = QAM_32.demodulate(np.asarray(sinal) / V, FC, AMOSTRAS_POR_SIMBOLO)
    return QAM_32.parallel_to_serial(QAM_32.decide(x, y), n_pad)

FISICAS = {
    # ---- banda base ----
    "NRZ polar": (
        lambda b, V: (nrz_polar.codificadorNRZPolar(b, V), 0),
        lambda s, V, n: nrz_polar.decodificadorNRZPolar(s, V)),
    "Bipolar": (
        lambda b, V: (bipolar.codificadorBipolar(len(b), b, V), 0),
        lambda s, V, n: bipolar.decodificadorBipolar(s, V)),
    "Manchester": (
        lambda b, V: (manchester.codificadorManchester(b, V, AMOSTRAS_POR_BIT), 0),
        lambda s, V, n: manchester.decodificadorManchester(s, V, AMOSTRAS_POR_BIT)),
    # ---- modulação por portadora ----
    "ASK": (
        lambda b, V: (ASK.modulacaoASK(b, F_ASK, V, AMOSTRAS_POR_BIT), 0),
        lambda s, V, n: ASK.demodulacaoASK(s, V, F_ASK, AMOSTRAS_POR_BIT)),
    "FSK": (
        lambda b, V: (FSK.modulacaoFSK(V, F1_FSK, F2_FSK, b, AMOSTRAS_POR_BIT), 0),
        lambda s, V, n: FSK.demodulacaoFSK(s, V, F1_FSK, F2_FSK, AMOSTRAS_POR_BIT)),
    "8-PSK": (_psk_tx, _psk_rx),
    "32-QAM": (_qam_tx, _qam_rx),
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
    if not texto:
        raise ValueError("digite uma mensagem")
    edc_tx, _, _ = EDCS[cfg.edc]
    enq_tx, _ = ENQUADRAMENTOS[cfg.enquadramento]
    fis_tx, _ = FISICAS[cfg.fisica]

    bits = texto_para_bits(texto)
    n = 8 * cfg.bytes_por_quadro
    bits_pad = bits + "0" * (-len(bits) % n)          # último quadro completo com 0s

    quadros = []
    for i in range(0, len(bits_pad), n):
        payload = bits_pad[i:i + n]
        dados = edc_tx(payload)
        quadros.append({"payload": payload, "dados": dados, "quadro": enq_tx(dados)})

    fluxo = "".join(q["quadro"] for q in quadros)
    sinal, n_pad = fis_tx(fluxo, cfg.V)
    return {"bits": bits, "quadros": quadros, "fluxo": fluxo,
            "sinal": np.asarray(sinal, dtype=float), "n_pad": n_pad}


def canal(sinal, cfg, semente=None):
    """Meio de transmissão: soma ruído gaussiano branco (AWGN) ao sinal."""
    if cfg.sigma <= 0:
        return np.array(sinal, dtype=float)
    return AWGN.canalAwgn(sinal, 0.0, cfg.sigma, semente)


def receber(sinal, n_pad, cfg):
    """Devolve um dict com tudo que o receptor recuperou (para mostrar na GUI)."""
    _, edc_rx, edc_tam = EDCS[cfg.edc]
    _, enq_rx = ENQUADRAMENTOS[cfg.enquadramento]
    _, fis_rx = FISICAS[cfg.fisica]

    fluxo = fis_rx(sinal, cfg.V, n_pad)
    tam = edc_tam(8 * cfg.bytes_por_quadro)            # tamanho esperado de payload+EDC

    quadros = []
    for conteudo in enq_rx(fluxo):
        dados = conteudo[:tam]                         # tira o padding de byte da contagem
        if len(dados) < tam:
            quadros.append({"dados": dados, "payload": None, "status": "truncado"})
            continue
        payload, ok, pos = edc_rx(dados)
        status = "ok" if ok else ("corrigido" if pos else "erro")
        quadros.append({"dados": dados, "payload": payload, "status": status})

    bits = "".join(q["payload"] for q in quadros if q["payload"] is not None)
    return {"fluxo": fluxo, "quadros": quadros, "bits": bits,
            "texto": bits_para_texto(bits)}


def bits_errados(a, b):
    """Quantos bits diferem entre dois fluxos (diferença de tamanho conta como erro)."""
    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))


if __name__ == "__main__":
    cfg = Config(fisica="8-PSK", sigma=0.3)
    tx = transmitir("Olá, rede!", cfg)
    rx = receber(canal(tx["sinal"], cfg, semente=1), tx["n_pad"], cfg)
    print("quadros:", [q["status"] for q in rx["quadros"]])
    print("recebido:", rx["texto"])
