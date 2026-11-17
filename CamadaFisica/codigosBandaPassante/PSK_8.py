# PSK_8.py
import math as mt
import numpy as np

cos_pi4 = mt.cos(mt.pi / 4)
sin_pi4 = mt.sin(mt.pi / 4)

# BitMapping que vai nos dar o canal i X(t) e o canal q y(t) para cada sequência de 3 bits
# Mapeamento 8-PSK circular em Código de Gray
PSK8 = {
    "000": (+1.0, 0.0), 
    "001": (+cos_pi4, +sin_pi4), 
    "011": (0.0, +1.0), 
    "010": (-cos_pi4, +sin_pi4),
    "110": (-1.0, 0.0), 
    "111": (-cos_pi4, -sin_pi4), 
    "101": (0.0, -1.0), 
    "100": (+cos_pi4, -sin_pi4)
}

INV_PSK8 = {v: k for k, v in PSK8.items()}                 # (x, y) -> bits
CONST_BITS = list(PSK8.keys())                             # 8 sequências de bits
CONST_PTS = np.array([PSK8[b] for b in CONST_BITS], float) # (8, 2) pontos ideais

def pad_bits(bits, m=3, fill="0"):
    """Completa o trem de bits até múltiplo de m. Retorna (bits, n_pad)."""
    n_pad = -len(bits) % m
    return bits + fill * n_pad, n_pad

def modulacao8PSK(bits, fc=4, As=400, T=1.0):

    nPad = -len(bits) % 3                        # verifica quantos bits falta para a mensagem ser um múltiplo de 3
    bits = bits + "0" * nPad                     # insere essa quantidade de bits 0

    bitsParalelo = [bits[k:k+3] for k in range(0,len(bits),3)]  # separa a mensagem em grupos de 3

    simbolos = [PSK8[g] for g in bitsParalelo]   # pega a representacao dele em i(t) e q(t) no nosso alfabeto
    
    t = np.arange(0, len(simbolos) * T, T/As)    # cria um vetor tempo que serão os instantes em que o sinal é calculado

    idx = np.minimum((t).astype(int), len(simbolos) - 1) # indexa as amostras para cada simbolo

    x = np.array([s[0] for s in simbolos])[idx]  # pega todos os valores do canal i x(t) 
    y = np.array([s[1] for s in simbolos])[idx]  # pega todos os valores do canal q y(t) 

    wc = 2 * np.pi * fc / T                      # calcula a frequência angular
    S = x * np.cos(wc * t) - y * np.sin(wc * t)  # calcula a portadora

    return nPad, t, x, y, simbolos, S


def demodulate(S, fc=4, fs=400, T=1.0):
    sps = int(round(fs * T))                  # amostras por símbolo
    n_symbols = len(S) // sps                 # deduz o nº de símbolos pelo tamanho de S
    S = S[:n_symbols * sps]                   # garante tamanho exato
    t = np.arange(len(S)) / fs                # vetor de tempo do receptor
    wc = 2 * np.pi * fc / T                   # frequência angular da portadora

    i_mix = S * np.cos(wc * t)                # mixer do ramo I
    q_mix = -S * np.sin(wc * t)               # mixer do ramo Q

    i_blocks = i_mix.reshape(n_symbols, sps)  # uma linha por símbolo
    q_blocks = q_mix.reshape(n_symbols, sps)

    x_hat = 2 * i_blocks.mean(axis=1)         # integra e normaliza -> x estimado
    y_hat = 2 * q_blocks.mean(axis=1)         # integra e normaliza -> y estimado
    
    return x_hat, y_hat

def decide(x_hat, y_hat):
    rx = np.column_stack((x_hat, y_hat))                                  # (N, 2)
    dist = np.linalg.norm(rx[:, None, :] - CONST_PTS[None, :, :], axis=2) # (N, 8) calcula distância para cada ponto
    return [CONST_BITS[k] for k in dist.argmin(axis=1)]

def parallel_to_serial(groups, n_pad=0):
    bits = "".join(groups)
    return bits[:len(bits) - n_pad] if n_pad else bits