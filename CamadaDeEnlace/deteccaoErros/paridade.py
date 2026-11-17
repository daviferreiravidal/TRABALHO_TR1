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