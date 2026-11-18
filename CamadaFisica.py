"""
CAMADA FÍSICA — implementações das funções da camada física.

    Codificação de banda base ... NRZ polar, Manchester, Bipolar
    Modulação por portadora ..... ASK, FSK, 8-PSK, 32-QAM
    Canal ....................... ruído AWGN

Transmissor: bits -> codificação -> modulação -> canal
Receptor:    sinal -> demodulação -> decodificação -> bits
"""

# Nomes que existiam em mais de um módulo e ganharam um sufixo ao serem
# reunidos neste arquivo (o corpo das funções não mudou):
#   nrz_polar.py                 NIVEIS               -> NIVEIS_NRZ_POLAR
#   nrz_polar.py                 CHIPS_POR_BIT        -> CHIPS_POR_BIT_NRZ_POLAR
#   manchester.py                NIVEIS               -> NIVEIS_MANCHESTER
#   manchester.py                CHIPS_POR_BIT        -> CHIPS_POR_BIT_MANCHESTER
#   bipolar.py                   NIVEIS               -> NIVEIS_BIPOLAR
#   bipolar.py                   CHIPS_POR_BIT        -> CHIPS_POR_BIT_BIPOLAR
#   PSK_8.py                     pad_bits             -> pad_bits_8PSK
#   PSK_8.py                     demodulate           -> demodulate8PSK
#   PSK_8.py                     decide               -> decide8PSK
#   PSK_8.py                     parallel_to_serial   -> parallel_to_serial_8PSK
#   PSK_8.py                     CONST_BITS           -> CONST_BITS_8PSK
#   PSK_8.py                     CONST_PTS            -> CONST_PTS_8PSK
#   QAM_32.py                    pad_bits             -> pad_bits_32QAM
#   QAM_32.py                    demodulate           -> demodulate32QAM
#   QAM_32.py                    decide               -> decide32QAM
#   QAM_32.py                    parallel_to_serial   -> parallel_to_serial_32QAM
#   QAM_32.py                    CONST_BITS           -> CONST_BITS_32QAM
#   QAM_32.py                    CONST_PTS            -> CONST_PTS_32QAM

import math
import math as mt
import numpy as np


# ===========================================================================
# Codificação NRZ polar
# (originalmente em CamadaFisica/codigosBandabase/nrz_polar.py)
# ===========================================================================
# NRZ polar: bit 1 -> +V, bit 0 -> -V (1 chip por bit)
NIVEIS_NRZ_POLAR = (-1, +1)        # níveis possíveis do sinal, em unidades de V
CHIPS_POR_BIT_NRZ_POLAR = 1

def codificadorNRZPolar( mensagem, V):
    Tam = len(mensagem)
    sinalNRZ = []

    for i in range(Tam):
        if mensagem[i] == '1':
            sinalNRZ.append(V)
        else:
            sinalNRZ.append(-V)

    return sinalNRZ

def decodificadorNRZPolar(Sinal, V):

    mensagem = []

    for i in range(len(Sinal)):
        if Sinal[i] > 0:
            mensagem.append('1')
        else:
            mensagem.append('0')

    return "".join(mensagem)


# ===========================================================================
# Codificação Manchester
# (originalmente em CamadaFisica/codigosBandabase/manchester.py)
# ===========================================================================
# manchester.py
# Manchester: cada bit vira 2 meios-bits (chips): 1 -> (+V, -V), 0 -> (-V, +V)
# Para modular por portadora usamos amostrasPorBit = CHIPS_POR_BIT = 2,
# ou seja, um valor por meio-bit; o modulador cuida das amostras da portadora.
NIVEIS_MANCHESTER = (-1, +1)        # níveis possíveis do sinal, em unidades de V
CHIPS_POR_BIT_MANCHESTER = 2

def codificadorManchester(mensagem, V, amostrasPorBit = 100):
    sinalManchester = []
    meio_bit = amostrasPorBit // 2
    
    for bit in mensagem:
        if bit == '1':
            # '1' representado por transição de +V para -V na metade do período
            sinalManchester.extend([V] * meio_bit)
            sinalManchester.extend([-V] * (amostrasPorBit - meio_bit))
        else:
            # '0' representado por transição de -V para +V na metade do período
            sinalManchester.extend([-V] * meio_bit)
            sinalManchester.extend([V] * (amostrasPorBit - meio_bit))
            
    return sinalManchester

def decodificadorManchester(sinal, V, amostrasPorBit = 100):
    mensagem = []
    nBits = len(sinal) // amostrasPorBit # divide o tamanho do sinal e arredonda para baixo
    meio_bit = amostrasPorBit // 2
    
    for i in range(nBits):
        # pega o bloco de amostras correspondente a um único bit
        bloco = sinal[i * amostrasPorBit: (i + 1) * amostrasPorBit]  
        
        # integra (soma) a primeira metade e a segunda metade do sinal
        soma_primeira_metade = sum(bloco[:meio_bit])
        soma_segunda_metade = sum(bloco[meio_bit:])
        
        # A decisão é feita baseada na transição: 
        # Se a energia inicial for maior que a final, foi +V para -V (Bit '1')
        if soma_primeira_metade > soma_segunda_metade:
            mensagem.append('1')
        else:
            mensagem.append('0')
            
    return "".join(mensagem)


# ===========================================================================
# Codificação Bipolar
# (originalmente em CamadaFisica/codigosBandabase/bipolar.py)
# ===========================================================================
# Bipolar (AMI): bit 0 -> 0, bit 1 -> +V e -V alternados (1 chip por bit)
NIVEIS_BIPOLAR = (-1, 0, +1)     # níveis possíveis do sinal, em unidades de V
CHIPS_POR_BIT_BIPOLAR = 1

def codificadorBipolar(Tam, mensagem,V):

    sinalBipolar = []
    amplitude = 1
    for i in range(Tam):
        if mensagem[i] == '1':
            if amplitude == 1:
                sinalBipolar.append(V)
                amplitude = -1
            else:
                sinalBipolar.append(-V)
                amplitude = 1
        else:
            sinalBipolar.append(0)
    return sinalBipolar

def decodificadorBipolar(Sinal, V):
    mensagem = []
    for i in range(len(Sinal)):
        if abs(Sinal[i]) > V/2:
            mensagem.append('1')
        else:
            mensagem.append('0')
    return "".join(mensagem)


# ===========================================================================
# Ferramentas de níveis (usadas pelos moduladores)
# (originalmente em CamadaFisica/codigosBandaPassante/niveis.py)
# ===========================================================================
# Ferramentas comuns aos moduladores: tratam o sinal JÁ CODIFICADO em banda base.
#
# O codificador (NRZ polar, Manchester ou Bipolar) entrega uma lista de "chips":
# um valor por intervalo de sinalização, sempre um dos níveis do código
# multiplicado por V. Exemplos com V = 1:
#     NRZ polar  "101" -> [ 1, -1,  1]          níveis (-1, +1)
#     Bipolar    "101" -> [ 1,  0, -1]          níveis (-1, 0, +1)
#     Manchester "10"  -> [ 1, -1, -1,  1]      níveis (-1, +1), 2 chips por bit
#
# Os moduladores trabalham com o ÍNDICE de cada nível no alfabeto do código:
#     NRZ/Manchester: -V -> 0, +V -> 1               (2 símbolos)
#     Bipolar:        -V -> 0,  0 -> 1, +V -> 2      (3 símbolos)

def indice(valor, V, niveis):
    """Índice do nível do alfabeto mais próximo de 'valor' (decisão por distância)."""
    x = valor / V
    return min(range(len(niveis)), key=lambda k: abs(x - niveis[k]))


def para_indices(sinal, V, niveis):
    return [indice(v, V, niveis) for v in sinal]


def para_sinal(indices, V, niveis):
    return [niveis[k] * V for k in indices]


def bits_por_chip(niveis):
    """Quantos bits são necessários para numerar os níveis (2 níveis -> 1, 3 níveis -> 2)."""
    return max(1, math.ceil(math.log2(len(niveis))))


def chips_para_bits(sinal, V, niveis):
    """Usado por 8-PSK e 32-QAM, que agrupam bits em símbolos:
    cada chip vira o número do seu nível escrito em binário."""
    b = bits_por_chip(niveis)
    return "".join(format(k, f"0{b}b") for k in para_indices(sinal, V, niveis))


def bits_para_chips(bits, V, niveis):
    """Inverso de chips_para_bits. Um número que não existe no alfabeto
    (ex.: '11' no bipolar, que só usa 00, 01 e 10) vira o maior nível."""
    b = bits_por_chip(niveis)
    indices = [min(int(bits[i:i + b], 2), len(niveis) - 1)
               for i in range(0, len(bits) - b + 1, b)]
    return para_sinal(indices, V, niveis)


# ===========================================================================
# Modulação ASK
# (originalmente em CamadaFisica/codigosBandaPassante/ASK.py)
# ===========================================================================
# ASK: a AMPLITUDE da portadora carrega o nível do sinal codificado.
#
# Recebe o sinal JÁ codificado em banda base (um valor por chip: -V, 0 ou +V)
# e transforma cada nível numa amplitude NÃO negativa:
#       A = V * (nivel/V + 1) / 2
#   2 níveis (NRZ, Manchester): -V -> 0,  +V -> V            (liga/desliga, OOK)
#   3 níveis (Bipolar):         -V -> 0,   0 -> V/2, +V -> V  (ASK de 3 níveis)
#
# sinal_codificado: lista de níveis (saída do codificador)
# V: amplitude máxima da portadora
# f: ciclos da portadora por chip
# amostrasPorChip: amostras geradas para cada chip


def modulaASK(sinal_codificado, V, niveis, f=4, amostrasPorChip=100):
    """Devolve (portadora, n_pad). No ASK não há padding: n_pad = 0."""
    portadora = []

    for nivel in sinal_codificado:
        A = V * (nivel / V + 1) / 2                                  # amplitude deste chip
        for j in range(amostrasPorChip):
            portadora.append(A * mt.sin(2 * mt.pi * f * j / amostrasPorChip))

    return portadora, 0


def demodulaASK(portadora, V, niveis, n_pad=0, f=4, amostrasPorChip=100):
    """Devolve o sinal codificado recuperado (um nível por chip), pronto
    para ir ao decodificador de banda base."""
    sinal = []
    nChips = len(portadora) // amostrasPorChip                       # arredonda para baixo

    for i in range(nChips):
        bloco = portadora[i * amostrasPorChip: (i + 1) * amostrasPorChip]

        # correlação com uma portadora de mesma fase e frequência -> amplitude
        soma = sum(x * mt.sin(2 * mt.pi * f * j / amostrasPorChip) for j, x in enumerate(bloco))
        A = 2 * soma / amostrasPorChip

        nivel = (2 * A / V - 1) * V                                  # desfaz A = V*(n/V+1)/2
        sinal.append(niveis[indice(nivel, V, niveis)] * V)           # decide o nível mais próximo

    return sinal


# ===========================================================================
# Modulação FSK
# (originalmente em CamadaFisica/codigosBandaPassante/FSK.py)
# ===========================================================================
# FSK: a FREQUÊNCIA da portadora carrega o nível do sinal codificado.
#
# Cada nível possível do código ganha uma frequência própria (em ciclos por chip):
#   2 níveis (NRZ, Manchester): -V -> 4,  +V -> 8
#   3 níveis (Bipolar):         -V -> 4,   0 -> 6,  +V -> 8
# Como as frequências têm um número inteiro de ciclos por chip, elas são
# ortogonais e o receptor consegue separá-las.
#
# Os parâmetros são:
# sinal_codificado = lista de níveis (saída do codificador)
# V = amplitude da portadora
# niveis = níveis possíveis do código (ex.: (-1, +1) ou (-1, 0, +1))
# f_min, f_max = menor e maior frequência usadas


def frequencias(niveis, f_min=4, f_max=8):
    """Uma frequência por nível, igualmente espaçadas entre f_min e f_max."""
    M = len(niveis)
    return [f_min + k * (f_max - f_min) / (M - 1) for k in range(M)]


def modulaFSK(sinal_codificado, V, niveis, amostras_por_chip=100, f_min=4, f_max=8):
    """Devolve (portadora, n_pad). No FSK não há padding: n_pad = 0."""
    portadora = []
    freqs = frequencias(niveis, f_min, f_max)

    for nivel in sinal_codificado:
        frequencia = freqs[indice(nivel, V, niveis)]
        for j in range(amostras_por_chip):
            portadora.append(V * mt.sin(2 * mt.pi * frequencia * j / amostras_por_chip))

    return portadora, 0


def demodulaFSK(portadora, V, niveis, n_pad=0, amostras_por_chip=100, f_min=4, f_max=8):
    """Devolve o sinal codificado recuperado (um nível por chip)."""
    sinal = []
    freqs = frequencias(niveis, f_min, f_max)
    nChips = len(portadora) // amostras_por_chip

    for i in range(nChips):
        bloco = portadora[i * amostras_por_chip: (i + 1) * amostras_por_chip]

        # Correlação E = I^2 + Q^2 com cada frequência candidata
        # (I = componente cosseno, Q = componente seno), assim a comparação
        # funciona independentemente da fase. Fica a frequência de maior energia.
        energias = []
        for fk in freqs:
            I = sum(x * mt.cos(2 * mt.pi * fk * j / amostras_por_chip) for j, x in enumerate(bloco))
            Q = sum(x * mt.sin(2 * mt.pi * fk * j / amostras_por_chip) for j, x in enumerate(bloco))
            energias.append(I ** 2 + Q ** 2)

        k = energias.index(max(energias))
        sinal.append(niveis[k] * V)

    return sinal


# ===========================================================================
# Modulação 8-PSK
# (originalmente em CamadaFisica/codigosBandaPassante/PSK_8.py)
# ===========================================================================
# PSK_8.py


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
CONST_BITS_8PSK = list(PSK8.keys())                             # 8 sequências de bits
CONST_PTS_8PSK = np.array([PSK8[b] for b in CONST_BITS_8PSK], float) # (8, 2) pontos ideais

def pad_bits_8PSK(bits, m=3, fill="0"):
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


def demodulate8PSK(S, fc=4, fs=400, T=1.0):
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

def decide8PSK(x_hat, y_hat):
    rx = np.column_stack((x_hat, y_hat))                                  # (N, 2)
    dist = np.linalg.norm(rx[:, None, :] - CONST_PTS_8PSK[None, :, :], axis=2) # (N, 8) calcula distância para cada ponto
    return [CONST_BITS_8PSK[k] for k in dist.argmin(axis=1)]

def parallel_to_serial_8PSK(groups, n_pad=0):
    bits = "".join(groups)
    return bits[:len(bits) - n_pad] if n_pad else bits


# ---------------------------------------------------------------------------
# Modulação do sinal JÁ CODIFICADO (NRZ polar, Manchester ou Bipolar)
#
# Cada chip do sinal codificado vira o número do seu nível em binário
# (2 níveis -> 1 bit por chip; 3 níveis, bipolar -> 2 bits por chip).
# Esses bits são agrupados de 3 em 3 e cada grupo vira um ponto da constelação.
# ---------------------------------------------------------------------------
def modula8PSK(sinal_codificado, V, niveis, fc=4, As=400):
    """Devolve (portadora, n_pad). n_pad = bits 0 acrescentados no último símbolo."""
    bits = chips_para_bits(sinal_codificado, V, niveis)
    n_pad, _t, _x, _y, _simbolos, S = modulacao8PSK(bits, fc, As)
    return V * S, n_pad


def demodula8PSK(portadora, V, niveis, n_pad, fc=4, As=400):
    """Devolve o sinal codificado recuperado (um nível por chip)."""
    x_hat, y_hat = demodulate8PSK(np.asarray(portadora) / V, fc, As)
    bits = parallel_to_serial_8PSK(decide8PSK(x_hat, y_hat), n_pad)
    return bits_para_chips(bits, V, niveis)


# ===========================================================================
# Modulação 32-QAM
# (originalmente em CamadaFisica/codigosBandaPassante/QAM_32.py)
# ===========================================================================
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

def pad_bits_32QAM(bits, m=5, fill="0"):
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
CONST_BITS_32QAM = list(QAM32.keys())                            # 32 sequências de bits
CONST_PTS_32QAM = np.array([QAM32[b] for b in CONST_BITS_32QAM], float)  # (32, 2) pontos ideais


def demodulate32QAM(S, fc=4, fs=400, T=1.0):
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

def decide32QAM(x_hat, y_hat):
    rx = np.column_stack((x_hat, y_hat))                                  # (N, 2)
    dist = np.linalg.norm(rx[:, None, :] - CONST_PTS_32QAM[None, :, :], axis=2) # (N, 32)
    return [CONST_BITS_32QAM[k] for k in dist.argmin(axis=1)]

def parallel_to_serial_32QAM(groups, n_pad=0):
    bits = "".join(groups)
    return bits[:len(bits) - n_pad] if n_pad else bits


# ---------------------------------------------------------------------------
# Modulação do sinal JÁ CODIFICADO (NRZ polar, Manchester ou Bipolar)
#
# Cada chip do sinal codificado vira o número do seu nível em binário
# (2 níveis -> 1 bit por chip; 3 níveis, bipolar -> 2 bits por chip).
# Esses bits são agrupados de 5 em 5 e cada grupo vira um ponto da constelação.
# ---------------------------------------------------------------------------
def modula32QAM(sinal_codificado, V, niveis, fc=4, As=400):
    """Devolve (portadora, n_pad). n_pad = bits 0 acrescentados no último símbolo."""
    bits = chips_para_bits(sinal_codificado, V, niveis)
    n_pad, _t, _x, _y, _simbolos, S = modulacao32QAM(bits, fc, As)
    return V * S, n_pad


def demodula32QAM(portadora, V, niveis, n_pad, fc=4, As=400):
    """Devolve o sinal codificado recuperado (um nível por chip)."""
    x_hat, y_hat = demodulate32QAM(np.asarray(portadora) / V, fc, As)
    bits = parallel_to_serial_32QAM(decide32QAM(x_hat, y_hat), n_pad)
    return bits_para_chips(bits, V, niveis)


# ===========================================================================
# Canal com ruído AWGN
# (originalmente em CamadaFisica/AWGN.py)
# ===========================================================================
def canalAwgn(sinal, media = 0.0, sigma = 1.0, semente=None):

    rng = np.random.default_rng(semente)
    sinal = np.asarray(sinal, dtype=float)
    ruido = rng.normal(loc=media, scale=sigma, size=sinal.shape)
    #loc é a média, scale o desvio padrão e size o tamanhao do veto

    return sinal + ruido
