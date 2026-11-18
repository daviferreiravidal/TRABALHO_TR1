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
NUM_COLUNAS = 8


def tamanho_quadro(tam_dados, num_colunas=NUM_COLUNAS):
    """Tamanho do quadro no canal para 'tam_dados' bits de payload+EDC."""
    return tam_dados + (-tam_dados % num_colunas)


def build_frame(dados, num_colunas=NUM_COLUNAS):
    """dados -> quadro entrelaçado (com zeros completando a última linha)."""
    quadro, _n_pad = entrelacarBits(dados, num_colunas)
    return quadro


def extract_frames(fluxo, tam_dados, num_colunas=NUM_COLUNAS):
    """Corta o fluxo em quadros de tamanho fixo e desentrelaça cada um.
    Devolve (payload + EDC) de cada quadro; uma sobra menor que um quadro
    no fim do fluxo é ignorada."""
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
