import math as mt

from .niveis import indice

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
