import math as mt

def checksum_transmissor(tamanho_do_segmento, input):
    #converte o input para uma string
    mensagem = ''.join(str(x) for x in input)

    #Calcula quantos segmentos serão usados
    n_segmentos = len(input)//tamanho_do_segmento
    
    soma = 0
    
    #Cria uma string de 1s com o tamanho do segmento -1
    mascara = (1 << tamanho_do_segmento) - 1
    
    #Loop de soma dos elementos
    for i in range(0, len(input), tamanho_do_segmento): 
        segmento = mensagem[i:(i+tamanho_do_segmento)]
        num = int(segmento, 2)
        soma += num

    #Descarta os bits de overflow
    soma &= mascara
    checksum = ~soma & mascara
    
    #Preenche com zeros se for menor que n(tamanho dos segmentos)
    checksum_bin = (bin(checksum)[2:].zfill(tamanho_do_segmento))
    mensagem += checksum_bin
    return mensagem


def checksum_receptor(tamanho_do_segmento, input):
    mensagem = ''.join(str(x) for x in input)

    soma = 0
    mascara = (1 << tamanho_do_segmento) - 1

    # Percorre todos os segmentos, incluindo o checksum
    for i in range(0, len(mensagem), tamanho_do_segmento):
        segmento = mensagem[i:i + tamanho_do_segmento]

        num = int(segmento, 2)
        soma += num

    # Descarta os bits de overflow
    soma &= mascara

    # Verifica se todos os bits são 1
    if soma == mascara:
        return "QUADRO SEM ERROS"
    else:
        return "QUADRO COM ERROS"
