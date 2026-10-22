import numpy as np

def canalAwgn(sinal, media = 0.0, sigma = 1.0, semente=None):

    rng = np.random.default_rng(semente)
    sinal = np.asarray(sinal, dtype=float)
    ruido = rng.normal(loc=media, scale=sigma, size=sinal.shape)
    #loc é a média, scale o desvio padrão e size o tamanhao do veto

    return sinal + ruido