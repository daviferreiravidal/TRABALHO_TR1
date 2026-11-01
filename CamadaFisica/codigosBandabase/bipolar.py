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
    return mensagem
