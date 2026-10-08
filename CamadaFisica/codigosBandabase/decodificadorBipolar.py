def decodificadorBipolar(Sinal, V):
    mensagem = []
    for i in range(len(Sinal)):
        if abs(Sinal[i]) > V/2:
            mensagem.append('1')
        else:
            mensagem.append('0')
    return mensagem