import math as mt   


def cc_transmissor(tamanho_maximo, input):

    # Converte a entrada para uma string de bits
    mensagem = ''.join(str(x) for x in input)

    # A contagem é feita em bytes: bits que não fecham um byte se perderiam
    if len(mensagem) % 8 != 0:
        raise ValueError("cc_transmissor: a mensagem precisa ter um número de bits múltiplo de 8")
    if not 1 <= tamanho_maximo <= 255:
        raise ValueError("cc_transmissor: o cabeçalho de 8 bits só conta de 1 a 255 bytes")

    mensagem_enquadrada = ''

    # Percorre a mensagem em blocos de bytes
    for i in range(0, len(mensagem), tamanho_maximo * 8):

        quadro = mensagem[i:i + tamanho_maximo * 8]

        # Calcula a quantidade de bytes do quadro
        tamanho = len(quadro) // 8

        # Cria o cabeçalho de 8 bits
        cabecalho = format(tamanho, '08b')

        mensagem_enquadrada += cabecalho + quadro

    return mensagem_enquadrada

def cc_receptor(input):

    # Converte a entrada para uma string de bits
    mensagem = ''.join(str(x) for x in input)

    quadros = []
    posicao = 0

    while posicao < len(mensagem):

        # Verifica se existe um cabeçalho completo
        if posicao + 8 > len(mensagem):
            break

        # Lê o header
        cabecalho = mensagem[posicao:posicao + 8]
        tamanho = int(cabecalho, 2)

        posicao += 8

        # Calcula o tamanho dos dados em bits
        tamanho_bits = tamanho * 8

        # Verifica se o quadro está completo
        if posicao + tamanho_bits > len(mensagem):
            break

        # Extrai o conteúdo do quadro
        quadro = mensagem[posicao:posicao + tamanho_bits]

        quadros.append(quadro)

        posicao += tamanho_bits

    return quadros
