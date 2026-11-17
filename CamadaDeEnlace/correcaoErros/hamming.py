
def qtdBase2(n):
    """Retorna a quantidade de bases de 2 em n."""
    qtd = 0
    for i in range(1,n+1):
        if i > 0 and (i & (i - 1)) == 0:   #faz o bitwise bit a bit. números que são potências de dois possuem apenas 1 bit 1
            qtd+=1

    return qtd

# retorna o tamanho da nossa palavra de código
def tamCodeWord(n):
    """Retorna o tamanho da codeWord de uma mensagem de n bits."""
    m = n
    m_anterior = 0
    while m_anterior != m:                  #se True significa que m não tem como mais crescer

        m_anterior = m                  
        m = n + qtdBase2(m_anterior)        #vê quantas bases de 2 tem em m_anterior

    return m

def calcularParidade(P, codeWord):
    """Calcula o bit de paridade P de uma codeWord."""
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
    """Retorna a codeWord de uma mensagem de bits usando o código de Hamming."""
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

    return codeWord

#retorna a posição do bit errado. Se retornar 0 todos os bits estão corretoscle
def hammingCodeReceptor(bits):
    paridades = []
    mensagem = []
    print(f"bites: , {bits}")
    for i in range(1,len(bits)+1):
        if i > 0 and (i & (i - 1)) == 0:      #se for uma potência de 2
            paridades.append(calcularParidade(i,bits))
        else:
            mensagem.append(bits[i-1])

    paridadesInversa = paridades[::-1]
    stringParidades = "".join(paridadesInversa)

    resultado = int(stringParidades,2)

    if resultado != 0:
        print("erro no " + str(resultado) + "º bit")
    else:
        print("chegou certinho!")

    return mensagem, resultado

#testes
if __name__ == "__main__":
    bits = "10101111"
    codeWord = hammingCode(bits)
    print("code hamming = " + "".join(codeWord) + "\n")

    print("caso positivo:")
    bits_recebidos,_ = hammingCodeReceptor(codeWord)

    print(bits_recebidos)

    print("caso negativo:")
    codeWord[4] = '1' if codeWord[4] == '0' else '0'    # flip no 5º bit
    hammingCodeReceptor(codeWord)


