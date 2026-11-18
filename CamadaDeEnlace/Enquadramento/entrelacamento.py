# entrelacamento.py
import math as mt

def entrelacarBits(bits, num_colunas=4):

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

NUM_COLUNAS = 8


def tamanho_quadro(tam_dados, num_colunas=NUM_COLUNAS):
    return tam_dados + (-tam_dados % num_colunas)


def build_frame(dados, num_colunas=NUM_COLUNAS):
    quadro, _n_pad = entrelacarBits(dados, num_colunas)
    return quadro


def extract_frames(fluxo, tam_dados, num_colunas=NUM_COLUNAS):
    tam = tamanho_quadro(tam_dados, num_colunas)
    n_pad = tam - tam_dados
    return [desentrelacarBits(fluxo[i:i + tam], num_colunas, n_pad)
            for i in range(0, len(fluxo) - tam + 1, tam)]


if __name__ == "__main__":
    dados = "1011001110001111010"
    q = build_frame(dados)
    print("dados:     ", dados)
    print("entrelaçado:", q)
    print("OK?:", extract_frames(q + q, len(dados)) == [dados, dados])
