import numpy as np

def canalAwgn(sinal, media = 0.0, sigma = 1.0, semente=None):
    """
    Canal AWGN: soma ruído gaussiano n ~ N(media, sigma²) ao sinal, amostra a amostra.

    Parâmetros:
    sinal (array): amostras de tensão (V) do sinal transmitido.
    media (float): média do ruído (V). Normalmente 0.
    sigma (float): desvio padrão do ruído (V). Define a potência do ruído.
    semente (int): opcional, para resultados reproduzíveis.

    Retorna:
    array: sinal recebido (V) = sinal + ruído.
    """
    rng = np.random.default_rng(semente)
    sinal = np.asarray(sinal, dtype=float)
    ruido = rng.normal(loc=media, scale=sigma, size=sinal.shape)
    #loc é a média, scale o desvio padrão e size o tamanhao do veto

    return sinal + ruido