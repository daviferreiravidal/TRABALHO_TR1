# entrelacamento.py
import math as mt

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