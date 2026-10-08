import math as mt

def modulacaoASK(sinal,f):
    portadora = []

    for bit in sinal:
        for j in range(100):
            portadora.append (bit * mt.sin(2 * mt.pi * f * j/100))

    return portadora