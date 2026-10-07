def CodificacaoBipolar(Tam, mensagem,V):
    """
    Função que realiza a codificação bipolar de um sinal binário.
    
    Parâmetros:
    Tam (int): Tamanho do sinal binário.
    mensagem (list): Lista contendo o sinal binário (0s e 1s).
    V (float): Valor de referência em volts para a codificação bipolar.
    
    Retorna:
    list: Lista contendo o sinal codificado em bipolar.
    """
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
