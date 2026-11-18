import math as mt

from .niveis import indice

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
