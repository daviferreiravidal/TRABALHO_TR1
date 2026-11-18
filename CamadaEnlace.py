"""
CAMADA DE ENLACE — implementações das funções da camada de enlace.

    Enquadramento ........ contagem de caracteres, inserção de bytes,
                           inserção de bits, entrelaçamento
    Detecção de erros .... bit de paridade, checksum, CRC-32
    Correção de erros .... código de Hamming

Transmissor: payload -> EDC -> enquadramento
Receptor:    desenquadramento -> verificação/correção do EDC -> payload
"""

# Nomes que existiam em mais de um módulo e ganharam um sufixo ao serem
# reunidos neste arquivo (o corpo das funções não mudou):
#   insercaoBytes.py             FLAG                 -> FLAG_BYTES
#   insercaoBytes.py             ESC                  -> ESC_BYTES
#   insercaoBytes.py             build_frame          -> build_frame_bytes
#   insercaoBytes.py             frame_message        -> frame_message_bytes
#   insercaoBytes.py             extract_frames       -> extract_frames_bytes
#   insercaoBytes.py             deframe_message      -> deframe_message_bytes
#   insercaoBits.py              FLAG                 -> FLAG_BITS
#   insercaoBits.py              build_frame          -> build_frame_bits
#   insercaoBits.py              frame_message        -> frame_message_bits
#   insercaoBits.py              extract_frames       -> extract_frames_bits
#   insercaoBits.py              deframe_message      -> deframe_message_bits
#   entrelacamento.py            NUM_COLUNAS          -> NUM_COLUNAS_ENTRELACAMENTO
#   entrelacamento.py            tamanho_quadro       -> tamanho_quadro_entrelacamento
#   entrelacamento.py            build_frame          -> build_frame_entrelacamento
#   entrelacamento.py            extract_frames       -> extract_frames_entrelacamento

import math as mt


# ===========================================================================
# Enquadramento: contagem de caracteres
# (originalmente em CamadaDeEnlace/Enquadramento/contagem_de_caracteres.py)
# ===========================================================================
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
    """Devolve SEMPRE uma lista com os quadros completos encontrados.
    Se o fluxo terminar no meio de um cabeçalho ou de um quadro
    (por exemplo, porque um erro corrompeu um cabeçalho), para ali e
    devolve o que já tinha conseguido ler."""

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


# ===========================================================================
# Enquadramento: inserção de bytes
# (originalmente em CamadaDeEnlace/Enquadramento/insercaoBytes.py)
# ===========================================================================
# Enquadramento por INSERÇÃO DE BYTES (byte stuffing), como no Tanenbaum.
#
# Cada quadro começa e termina com um byte especial FLAG. Se o próprio dado
# contiver um byte igual a FLAG ou a ESC, o transmissor insere um ESC antes dele;
# o receptor, ao ver um ESC, descarta-o e aceita o byte seguinte como dado comum.
#
#     dados:   41  7E  42  7D  43
#     quadro:  7E  41  7D 7E  42  7D 7D  43  7E
#              ^FLAG   ^ESC        ^ESC       ^FLAG
#
# Entradas e saídas são strings de bits ("0110..."), com tamanho múltiplo de 8.

FLAG_BYTES = "01111110"   # 0x7E
ESC_BYTES = "01111101"    # 0x7D


def _bytes(bits):
    if len(bits) % 8 != 0:
        raise ValueError("inserção de bytes: o número de bits precisa ser múltiplo de 8")
    return [bits[i:i + 8] for i in range(0, len(bits), 8)]


# ---------------- Transmissor ----------------
def byte_stuff(payload):
    """Insere um ESC antes de cada byte igual a FLAG ou ESC."""
    saida = []
    for byte in _bytes(payload):
        if byte in (FLAG_BYTES, ESC_BYTES):
            saida.append(ESC_BYTES)
        saida.append(byte)
    return "".join(saida)


def build_frame_bytes(payload):
    """Encapsula um payload em um quadro: FLAG + payload com stuffing + FLAG."""
    return FLAG_BYTES + byte_stuff(payload) + FLAG_BYTES


def frame_message_bytes(bits, max_bytes=8):
    """Fragmenta a mensagem em payloads de até max_bytes bytes e gera o fluxo de quadros."""
    passo = 8 * max_bytes
    return "".join(build_frame_bytes(bits[k:k + passo]) for k in range(0, len(bits), passo))


# ---------------- Receptor ----------------
def extract_frames_bytes(stream):
    """Varre o fluxo byte a byte e devolve a lista de payloads (já sem os ESC).

    Toda FLAG fecha o quadro que estava aberto (se houver algo nele) e abre
    um novo. Assim, "FLAG dados FLAG FLAG dados FLAG" vira dois quadros, e se
    uma FLAG for corrompida pelo ruído o receptor se ressincroniza na próxima.
    Bits que sobram no fim (menos de 1 byte) são ignorados.
    """
    payloads = []
    buf = []
    dentro = False          # já vimos a primeira FLAG?
    escapando = False       # o byte anterior era um ESC?

    for i in range(0, len(stream) - 7, 8):
        byte = stream[i:i + 8]
        if escapando:                       # byte depois do ESC: é dado, seja o que for
            buf.append(byte)
            escapando = False
        elif byte == FLAG_BYTES:
            if dentro and buf:
                payloads.append("".join(buf))
            buf, dentro = [], True
        elif byte == ESC_BYTES:
            escapando = True
        elif dentro:
            buf.append(byte)
    return payloads


def deframe_message_bytes(stream):
    return "".join(extract_frames_bytes(stream))


# ---------------- Teste ----------------


# ===========================================================================
# Enquadramento: inserção de bits
# (originalmente em CamadaDeEnlace/Enquadramento/insercaoBits.py)
# ===========================================================================
FLAG_BITS = "01111110"

# ---------------- Transmissor ----------------
def bit_stuff(payload):
    """Insere um '0' após cada 5 uns consecutivos."""
    out, ones = [], 0
    for b in payload:
        out.append(b)
        if b == "1":
            ones += 1
            if ones == 5:
                out.append("0")      # bit inserido
                ones = 0
        else:
            ones = 0
    return "".join(out)

def build_frame_bits(payload):
    """Encapsula um payload em um quadro: FLAG + payload com stuffing + FLAG."""
    return FLAG_BITS + bit_stuff(payload) + FLAG_BITS

def frame_message_bits(bits, max_payload=64):
    """Fragmenta a mensagem em payloads de até max_payload bits e gera o fluxo de quadros."""
    frames = [build_frame_bits(bits[k:k + max_payload])
              for k in range(0, len(bits), max_payload)]
    return "".join(frames)

# ---------------- Receptor ----------------
def extract_frames_bits(stream):
    """Varre o fluxo de bits e devolve a lista de payloads (já sem stuffing)."""
    payloads = []
    buf = []            # bits acumulados do quadro atual
    ones = 0            # quantidade de 1s consecutivos
    in_frame = False    # True depois de ver a primeira flag

    for b in stream:
        if b == "1":
            ones += 1
            buf.append("1")
            if ones >= 7:                 # 7 uns seguidos: erro/abort
                buf, ones, in_frame = [], 0, False
        else:  # b == "0"
            if ones == 5:                 # '0' inserido pelo stuffing: descarta
                ones = 0
            elif ones == 6:               # 0 + 111111 + 0 = flag
                if in_frame and len(buf) > 7:
                    payloads.append("".join(buf[:-7]))   # tira o 0 inicial e os 6 uns da flag
                buf, ones, in_frame = [], 0, True        # começa um novo quadro
            else:                         # '0' normal
                buf.append("0")
                ones = 0
    return payloads

def deframe_message_bits(stream):
    return "".join(extract_frames_bits(stream))

# ---------------- Teste ----------------


# ===========================================================================
# Enquadramento: entrelaçamento
# (originalmente em CamadaDeEnlace/Enquadramento/entrelacamento.py)
# ===========================================================================
# entrelacamento.py

def entrelacarBits(bits, num_colunas=4):
    """
    Realiza o entrelaçamento matricial (escreve por linha, lê por coluna).
    Retorna (bits_entrelacados, n_pad).
    """
    # Calcula o padding necessário para fechar a matriz completa (múltiplo de num_colunas)
    n_pad = -len(bits) % num_colunas
    bits_padded = bits + "0" * n_pad
    
    num_linhas = len(bits_padded) // num_colunas
    
    # Monta a matriz escrevendo linha por linha
    matriz = [
        bits_padded[i * num_colunas : (i + 1) * num_colunas] 
        for i in range(num_linhas)
    ]
    
    # Lê coluna por coluna para gerar a sequência entrelaçada
    bits_entrelacados = ""
    for col in range(num_colunas):
        for lin in range(num_linhas):
            bits_entrelacados += matriz[lin][col]
            
    return bits_entrelacados, n_pad


def desentrelacarBits(bits_entrelacados, num_colunas=4, n_pad=0):
    """
    Desfaz o entrelaçamento matricial (escreve por coluna, lê por linha) e remove o padding.
    """
    if len(bits_entrelacados) % num_colunas != 0:
        raise ValueError("O tamanho dos bits recebidos não é múltiplo do número de colunas.")
        
    num_linhas = len(bits_entrelacados) // num_colunas
    
    # Reconstrói a matriz preenchendo coluna por coluna
    matriz = [['' for _ in range(num_colunas)] for _ in range(num_linhas)]
    idx = 0
    for col in range(num_colunas):
        for lin in range(num_linhas):
            matriz[lin][col] = bits_entrelacados[idx]
            idx += 1
            
    # Lê linha por linha para recuperar a ordem original
    bits_recuperados = "".join("".join(linha) for linha in matriz)
    
    # Remove os bits de padding adicionados no transmissor
    if n_pad > 0:
        bits_recuperados = bits_recuperados[:-n_pad]
        
    return bits_recuperados


# ---------------------------------------------------------------------------
# Enquadramento por entrelaçamento (quadros de tamanho fixo)
#
# O entrelaçamento não tem FLAG nem cabeçalho, então os quadros têm TAMANHO
# FIXO, combinado entre transmissor e receptor: cada quadro é a matriz
# (payload + EDC) de NUM_COLUNAS colunas, lida coluna por coluna. O receptor
# corta o fluxo em blocos desse tamanho e desfaz a matriz de cada um.
#
# Vantagem: uma rajada de erros vizinhos no canal cai em linhas diferentes da
# matriz, ou seja, fica espalhada pelo quadro depois do desentrelaçamento.
# Limitação: se o receptor perder ou ganhar um bit, todos os quadros
# seguintes ficam desalinhados (não há como se ressincronizar).
# ---------------------------------------------------------------------------
NUM_COLUNAS_ENTRELACAMENTO = 8


def tamanho_quadro_entrelacamento(tam_dados, num_colunas=NUM_COLUNAS_ENTRELACAMENTO):
    """Tamanho do quadro no canal para 'tam_dados' bits de payload+EDC."""
    return tam_dados + (-tam_dados % num_colunas)


def build_frame_entrelacamento(dados, num_colunas=NUM_COLUNAS_ENTRELACAMENTO):
    """dados -> quadro entrelaçado (com zeros completando a última linha)."""
    quadro, _n_pad = entrelacarBits(dados, num_colunas)
    return quadro


def extract_frames_entrelacamento(fluxo, tam_dados, num_colunas=NUM_COLUNAS_ENTRELACAMENTO):
    """Corta o fluxo em quadros de tamanho fixo e desentrelaça cada um.
    Devolve (payload + EDC) de cada quadro; uma sobra menor que um quadro
    no fim do fluxo é ignorada."""
    tam = tamanho_quadro_entrelacamento(tam_dados, num_colunas)
    n_pad = tam - tam_dados
    return [desentrelacarBits(fluxo[i:i + tam], num_colunas, n_pad)
            for i in range(0, len(fluxo) - tam + 1, tam)]


# ===========================================================================
# Detecção de erros: bit de paridade
# (originalmente em CamadaDeEnlace/deteccaoErros/paridade.py)
# ===========================================================================
# paridade.py

def adicionarBitParidade(bits, tipo='par'):
    """
    Adiciona um bit de paridade ao final da sequência de bits.
    tipo: 'par' (even) ou 'impar' (odd)
    """
    qtd_uns = bits.count('1')
    
    if tipo == 'par':
        # Se a quantidade de '1's já for par, adiciona '0'; senão, adiciona '1'
        bit_paridade = '0' if (qtd_uns % 2 == 0) else '1'
    elif tipo == 'impar':
        # Se a quantidade de '1's for ímpar, adiciona '0'; senão, adiciona '1'
        bit_paridade = '0' if (qtd_uns % 2 != 0) else '1'
    else:
        raise ValueError("Tipo de paridade inválido. Use 'par' ou 'impar'.")
        
    return bits + bit_paridade


def verificarBitParidade(quadro, tipo='par'):
    """
    Verifica se houve erro no quadro recebido e retorna (valido, dados_originais).
    """
    if len(quadro) < 2:
        raise ValueError("O quadro deve conter dados e o bit de paridade.")
        
    dados = quadro[:-1]
    bit_recebido = quadro[-1]
    
    # Recalcula a paridade esperada com base nos dados recebidos
    quadro_esperado = adicionarBitParidade(dados, tipo)
    bit_esperado = quadro_esperado[-1]
    
    valido = (bit_recebido == bit_esperado)
    
    return valido, dados


# ===========================================================================
# Detecção de erros: checksum
# (originalmente em CamadaDeEnlace/deteccaoErros/checksum.py)
# ===========================================================================
def checksum_transmissor(tamanho_do_segmento, input):
    #converte o input para uma string
    mensagem = ''.join(str(x) for x in input)

    #Se o último segmento ficar incompleto, o receptor (que soma a mensagem
    #já com o checksum no fim) desalinha os segmentos e acusa erro sempre
    if len(mensagem) % tamanho_do_segmento != 0:
        raise ValueError("checksum: o tamanho da mensagem precisa ser múltiplo do tamanho do segmento")

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

    # Verifica se todos os bits são 1  (True = quadro sem erros)
    return soma == mascara


# ===========================================================================
# Detecção de erros: CRC-32
# (originalmente em CamadaDeEnlace/deteccaoErros/crc.py)
# ===========================================================================
POLY = 0x04C11DB7
R = 32
MASK = 0xFFFFFFFF

def crc_transmissor(bits):
    bits_aux = bits + ('0' * R)

    # janela inicial: primeiros 32 bits da mensagem aumentada
    crc = int(bits_aux[:32], 2)

    # traz um bit por vez (um deslocamento por bit restante)
    for b in range(32, len(bits_aux)):
        top = (crc >> 31) & 1                        # bit que vai "transbordar"
        crc = ((crc << 1) | int(bits_aux[b])) & MASK # desloca, traz o próximo bit, limita a 32 bits
        if top:
            crc ^= POLY

    return crc

def crc_receptor(bits):

    rest = int(bits[:32],2)

    for b in range(32, len(bits)):
        top = (rest >> 31) & 1
        rest = ((rest << 1) | int(bits[b])) & MASK
        if top:
            rest ^= POLY

    return rest == 0


#testes


# ===========================================================================
# Correção de erros: código de Hamming
# (originalmente em CamadaDeEnlace/correcaoErros/hamming.py)
# ===========================================================================
def qtdBase2(n):
    qtd = 0
    for i in range(1,n+1):
        if i > 0 and (i & (i - 1)) == 0:   #faz o bitwise bit a bit. números que são potências de dois possuem apenas 1 bit 1
            qtd+=1

    return qtd

# retorna o tamanho da nossa palavra de código
def tamCodeWord(n):
    m = n
    m_anterior = 0
    while m_anterior != m:                  #se True significa que m não tem como mais crescer

        m_anterior = m                  
        m = n + qtdBase2(m_anterior)        #vê quantas bases de 2 tem em m_anterior

    return m

def calcularParidade(P, codeWord):

    intCodeWord = [int(x) for x in codeWord]        #converte a string de bits em uma lista de inteiros
    paridade = 0
    for i in range(P-1,len(codeWord),2*(P)):        #percorre nosso codeWord somando P casas apartir de P e pulando P casas depois
        paridade += sum(intCodeWord[i:(i+P)])

    if paridade % 2 == 0:                           #paridade Par
        return '0'
    else:
        return '1'
    
#retornar a codeWord de uma mansagem de bits
def hammingCode(bits):

    n = len(bits)
    m = tamCodeWord(n)

    codeWordSemParidade = []

    i_bits = 0
    for i in range(1,m+1):
        if i > 0 and (i & (i - 1)) == 0:      #se for uma potência de 2
            codeWordSemParidade.append('0')                #adiciona um zero para calcularmos a paridade depois
        else:
            codeWordSemParidade.append(bits[i_bits])       #se não adiciona um bit da mensagem
            i_bits+=1

    codeWord = codeWordSemParidade.copy()                  
    for i in range (1,m+1):
        if i > 0 and (i & (i - 1)) == 0:                                #Se for potência de 2 é um bit de paridade
            codeWord[i-1] = calcularParidade(i,codeWordSemParidade)     #calcula o bit de paridade e põe ele no nosso codeWord final

    return "".join(codeWord)                                        #devolve string, como os outros módulos

#retorna a posição do bit errado. Se retornar 0 todos os bits estão corretos
def hammingCodeReceptor(bits):
    paridades = []

    for i in range(1,len(bits)+1):
        if i > 0 and (i & (i - 1)) == 0:      #se for uma potência de 2
            paridades.append(calcularParidade(i,bits))

    paridadesInversa = paridades[::-1]
    stringParidades = "".join(paridadesInversa)

    resultado = int(stringParidades,2)

    return resultado

#corrige (se der) o bit errado e devolve (dados, posicao_do_erro)
#posicao_do_erro = 0 significa que chegou certinho
def hammingDecodifica(codeWord):
    pos = hammingCodeReceptor(codeWord)
    bits = list(codeWord)

    if 0 < pos <= len(bits):                    #com 2+ erros a síndrome pode apontar para fora da codeWord
        bits[pos-1] = '1' if bits[pos-1] == '0' else '0'

    dados = "".join(b for i, b in enumerate(bits, start=1) if (i & (i - 1)) != 0)  #tira as posições potência de 2
    return dados, pos

#testes


# ===========================================================================
# Testes de cada módulo:  python CamadaEnlace.py
# ===========================================================================
if __name__ == "__main__":
    # ---------- Enquadramento: inserção de bytes ----------
    print('--- Enquadramento: inserção de bytes ---')
    def b(*hexas):
        return "".join(format(h, "08b") for h in hexas)

    msg = b(0x41, 0x7E, 0x42, 0x7D, 0x43)
    quadro = build_frame_bytes(msg)
    print("Quadro:", " ".join(f"{int(quadro[i:i+8], 2):02X}" for i in range(0, len(quadro), 8)))
    print("OK?:", extract_frames_bytes(quadro) == [msg])

    longa = b(*range(256))
    print("Ida-volta com todos os bytes 00..FF:", deframe_message_bytes(frame_message_bytes(longa, 5)) == longa)

    # ---------- Enquadramento: inserção de bits ----------
    print('--- Enquadramento: inserção de bits ---')
    msg = "0000010011111100100100010111010" + "1111111111" + "01111110"
    tx = frame_message_bits(msg, max_payload=16)
    rx = deframe_message_bits(tx)

    print("Fluxo transmitido:", tx)
    print("Mensagem original:", msg)
    print("Mensagem recebida:", rx)
    print("OK?:", rx == msg)

    # Verificação do stuffing
    print(bit_stuff("0111111011111"))   # -> 01111101011111 0? veja a saída
    assert "111111" not in bit_stuff("1" * 40)

    # ---------- Enquadramento: entrelaçamento ----------
    print('--- Enquadramento: entrelaçamento ---')
    dados = "1011001110001111010"
    q = build_frame_entrelacamento(dados)
    print("dados:     ", dados)
    print("entrelaçado:", q)
    print("OK?:", extract_frames_entrelacamento(q + q, len(dados)) == [dados, dados])

    # ---------- Detecção de erros: CRC-32 ----------
    print('--- Detecção de erros: CRC-32 ---')
    bits = "10110"
    result = crc_transmissor(bits)
    print(hex(result))                 # 0x569796c2
    print(format(result, '032b'))      # 01010110100101111001011011000010

    #caso bom
    print(bits + " + " + format(result, '032b'))
    bits = bits + format(result, '032b')

    print(bits)

    if crc_receptor(bits):
        print("bits sem erro")
    else:
        print("bits com erro")

    #caso ruim

    bits_corrompidos = "00110" + format(result, '032b')

    if crc_receptor(bits_corrompidos):
        print("bits sem erro")
    else:
        print("bits com erro")

    # ---------- Correção de erros: código de Hamming ----------
    print('--- Correção de erros: código de Hamming ---')
    bits = "1101001"
    codeWord = hammingCode(bits)
    print("code hamming = " + codeWord + "\n")

    print("caso positivo:")
    print(hammingDecodifica(codeWord))

    print("caso negativo:")
    errada = list(codeWord)
    errada[4] = '1' if errada[4] == '0' else '0'        # flip no 5º bit
    print(hammingDecodifica("".join(errada)))
