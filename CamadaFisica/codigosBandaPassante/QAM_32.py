import math as mt
import numpy as np
import matplotlib as mp

#BitMapping que vai nos dar o canal i X(t) e o canal q y(t) para cada sequência de bits
QAM32 = {
    "00000": (+1, +1), "00001": (+3, +1), "00010": (+3, +5), "00011": (+5, +1),
    "00100": (+1, +3), "00101": (+3, +3), "00110": (+1, +5), "00111": (+5, +3),
    "01000": (+1, -1), "01001": (+3, -1), "01010": (+3, -5), "01011": (+5, -1),
    "01100": (+1, -3), "01101": (+3, -3), "01110": (+1, -5), "01111": (+5, -3),
    "10000": (-1, +1), "10001": (-3, +1), "10010": (-3, +5), "10011": (-5, +1),
    "10100": (-1, +3), "10101": (-3, +3), "10110": (-1, +5), "10111": (-5, +3),
    "11000": (-1, -1), "11001": (-3, -1), "11010": (-3, -5), "11011": (-5, -1),
    "11100": (-1, -3), "11101": (-3, -3), "11110": (-1, -5), "11111": (-5, -3),
}

def pad_bits(bits, m=5, fill="0"):
    """Completa o trem de bits até múltiplo de m. Retorna (bits, n_pad)."""
    n_pad = -len(bits) % m
    return bits + fill * n_pad, n_pad


def modulacao32QAM(bits, fc = 4, As=400,T = 1.0):


    nPad = -len(bits) % 5 #verifica quantos bits falta para a mensagem ser um múltiplo de 5
    bits = bits + "0"*nPad       #insere essa quantidade de bits 0

    bitsParalelo = [bits[k:k+5] for k in range(0,len(bits),5)]  #separa a mensagem em grupos de 5

    simbolos = [QAM32[g] for g in bitsParalelo] #usando o cada sequencia de 5 bits separada como chave
                                                #pegamos a representacao dele em i(t) e q(t) no nosso alfabeto
    
    t = np.arange(0, len(simbolos) * T, T/As) #cria um vetor tempo que serão os instantes em que o sinal é calculado

    idx = np.minimum((t).astype(int), len(simbolos) - 1) #indexa as amostras para cada simbolo

    x = np.array([s[0] for s in simbolos])[idx] #pega todos os valores do canal i x(t) das sequencias de bits que separamos
    y = np.array([s[1] for s in simbolos])[idx] #pega todos os valores do canal q y(t) das sequencias de bits que separamos

    wc = 2*np.pi * fc/T #calcula a frequência angular
    S = x * np.cos(wc * t) - y * np.sin(wc * t)  #calcula a portadora

    return nPad,t, x, y, simbolos, S

INV_QAM32 = {v: k for k, v in QAM32.items()}               # (x, y) -> bits
CONST_BITS = list(QAM32.keys())                            # 32 sequências de bits
CONST_PTS = np.array([QAM32[b] for b in CONST_BITS], float)  # (32, 2) pontos ideais


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
    dist = np.linalg.norm(rx[:, None, :] - CONST_PTS[None, :, :], axis=2) # (N, 32)
    return [CONST_BITS[k] for k in dist.argmin(axis=1)]

def parallel_to_serial(groups, n_pad=0):
    bits = "".join(groups)
    return bits[:len(bits) - n_pad] if n_pad else bits