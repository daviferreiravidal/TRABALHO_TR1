
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
if __name__ == "__main__":
    bits = "1101001"
    codeWord = hammingCode(bits)
    print("code hamming = " + codeWord + "\n")

    print("caso positivo:")
    print(hammingDecodifica(codeWord))

    print("caso negativo:")
    errada = list(codeWord)
    errada[4] = '1' if errada[4] == '0' else '0'        # flip no 5º bit
    print(hammingDecodifica("".join(errada)))
