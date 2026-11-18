import math as mt
#sinal é a nossa mensagem que vamos transmitir
#f a frenquecia do sinal
#V a amplitude em volts da nossa portadora

def modulacaoASK(sinal, f, V, amostrasPorBit = 100):
    portadora = []

    for bit in sinal:
        bit = int(bit)                                                  # aceita '0'/'1' ou 0/1
        for j in range(amostrasPorBit):                                 # amostras por bit
            portadora.append (V * bit * mt.sin(2 * mt.pi * f * j/amostrasPorBit))

    return portadora

def demodulacaoASK(portadora, V, f, amostrasPorBit = 100,):
    bits = []
    nBits = len(portadora) // amostrasPorBit # vai dividir o tamanho da portadora e arrendondar para baixo

    for i in range(nBits):
        bloco = portadora[i * amostrasPorBit: (i + 1) * amostrasPorBit]  # pega o bloco de amostras do bit

        soma = sum(x * mt.sin(2 * mt.pi * f * j / amostrasPorBit) # faz a correlação entre a amostra e um sinal da mesma fase e frequência para 
                   for j, x in enumerate(bloco))                  # para conseguirmos a amplitude
        
        a = 2 * soma / amostrasPorBit      # amplitude estimada (com sinal)

        if abs(a) > (V / 2):
            bits.append('1')
        else:
            bits.append('0')

    return "".join(bits)