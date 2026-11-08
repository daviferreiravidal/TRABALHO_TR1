import math as mt

#A modulação FSK representa mensagens a partir da modulação
#de frequência da portadora.

#Os parâmetros da função abaixo são: 
#A = Amplitude da Portadora
#f1 = Frequência da portadora para o bit 1
#f2 = Frequência da portadora para o bit 0
#mensagem = sequência de bits a ser transmitida

def modulacaoFSK(A, f1, f2, mensagem, amostras_por_bit):
    portadora = []
    frequencia = 0
    
    for bit in mensagem:
        if bit == 1:
            frequencia = f1
        else:
            frequencia = f2
        for j in range(amostras_por_bit):
            portadora.append(A*mt.sin(2*mt.pi*frequencia*j/amostras_por_bit))

    return portadora

def demodulacaoFSK(portadora, A, f1, f2, amostras_por_bit):
    bits_stream = []
    nBits = len(portadora) // amostras_por_bit

    for i in range(nBits):
        bloco = portadora[i*amostras_por_bit: (i+1)*amostras_por_bit]       
        
        #Usei a correlação de sinais dada por E = I^2 + Q^2
        #Onde I é a componente cosseno e Q a componente seno do sinal
        #Assim a comparação funciona independentemente da fase
        #Fiz isso comparando com um sinal com a frequência f1, logo temos I1 E Q2
        #E o mesmo para um sinal com frequência f2                                                                    
        
        I1 = sum(x*mt.cos(2*mt.pi*f1*j/amostras_por_bit)
                        for j, x in enumerate(bloco))
        
        Q1 = sum(x*mt.sin(2*mt.pi*f1*j/amostras_por_bit)
                        for j, x in enumerate(bloco))        
        
        I2 = sum(x*mt.cos(2*mt.pi*f2*j/amostras_por_bit)
                                for j, x in enumerate(bloco))
                
        Q2 = sum(x*mt.sin(2*mt.pi*f2*j/amostras_por_bit)
                        for j, x in enumerate(bloco)) 

        caso1 = I1**2 + Q1**2
        caso2 = I2**2 + Q2**2
        
        if abs(caso1) > abs(caso2):
            bits_stream.append(1)
        else:
            bits_stream.append(0)

    return bits_stream   

    