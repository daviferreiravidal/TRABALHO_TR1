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

def serial_to_parallel(bits, m=5):
    """Corta o trem de bits em grupos de m bits (um por símbolo)."""
    return [bits[k:k+m] for k in range(0, len(bits), m)]

def map_symbols(groups):
    """Associação de coordenadas: grupo de 5 bits -> (x, y)."""
    return [QAM32[g] for g in groups]

def modulate(symbols, fc=4, fs=400, T=1.0):
    """Gera x(t), y(t) e S(t) a partir da lista de (x, y)."""
    import numpy as np
    N = len(symbols)
    t = np.arange(0, N * T, T / fs)
    idx = np.minimum((t / T).astype(int), N - 1)
    x = np.array([s[0] for s in symbols])[idx]
    y = np.array([s[1] for s in symbols])[idx]
    wc = 2 * np.pi * fc / T
    S = x * np.cos(wc * t) - y * np.sin(wc * t)
    return t, x, y, S

#---------------------------//------------------------------------------------------

#meus códigos

def modulacao32QAM(bits, fc = 4, As=400):


    nPad = -len(bits) % 5 #verifica quantos bits falta para a mensagem ser um múltiplo de 5
    bits + "0"*nPad       #insere essa quantidade de bits 0

    bitsParalelo = [bits[k:k+5] for k in range(0,len(bits),5)]  #separa e mensagem em grupos de 5

    simbolos = [QAM32[g] for g in bitsParalelo] #usando o cada sequencia de 5 bits separada como chave
                                                #pegamos a representacao dele em i(t) e q(t) no nosso alfabeto
    
    t = np.arange(0, len(simbolos), 1/As) #cria um vetor tempo que serão os instantes em que o sinal é calculado

    idx = np.minimum((t).astype(int), len(simbolos) - 1) #indexa as amostras para cada simbolo

    x = np.array([s[0] for s in simbolos])[idx] #pega todos os valores do canal i x(t) das sequencias de bits que separamos
    y = np.array([s[1] for s in simbolos])[idx] #pega todos os valores do canal q y(t) das sequencias de bits que separamos

    wc = 2*np.pi * fc #calcula a frequência angular
    S = x * np.cos(wc * t) - y * np.sin(wc * t)  #calcula a portadora

    return t, x, y, S
