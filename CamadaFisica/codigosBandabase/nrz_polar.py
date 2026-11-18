# NRZ polar: bit 1 -> +V, bit 0 -> -V (1 chip por bit)
NIVEIS = (-1, +1)        # níveis possíveis do sinal, em unidades de V
CHIPS_POR_BIT = 1

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