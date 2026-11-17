import numpy as np
import matplotlib.pyplot as plt
from codigosBandaPassante.QAM_32 import *
from AWGN import canalAwgn



def plot_signals(t, x, y, S, T=1.0, n_symbols=None):
    """Plota x(t), y(t) e o sinal modulado S(t)."""
    fig, axs = plt.subplots(4, 1, figsize=(12, 9), sharex=True)

    axs[0].step(t, x, where="post", color="tab:blue")
    axs[0].set_ylabel("x(t)  [canal I]")
    axs[0].set_title("Canal em fase (I)")

    axs[1].step(t, y, where="post", color="tab:orange")
    axs[1].set_ylabel("y(t)  [canal Q]")
    axs[1].set_title("Canal em quadratura (Q)")

    axs[2].plot(t, S, color="tab:green", linewidth=1)
    axs[2].set_ylabel("S(t)")
    axs[2].set_xlabel("Tempo (t/T)")
    axs[2].set_title("Sinal modulado 32-QAM")

    axs[3].plot(t, canalAwgn(S), color="tab:green", linewidth=1)
    axs[3].set_ylabel("S(t) + Ruído")
    axs[3].set_xlabel("Tempo (t/T)")
    axs[3].set_title("Sinal modulado 32-QAM + ruído")

    # Linhas verticais marcando o início de cada símbolo
    if n_symbols is not None:
        for ax in axs:
            for k in range(n_symbols + 1):
                ax.axvline(k * T, color="gray", linestyle="--", linewidth=0.5)
            ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

# Uso
bits_original = "0000010011111100100100010111010"

bits, n_pad = pad_bits(bits_original)  
"""                  # 35 bits, n_pad = 4
groups = serial_to_parallel(bits_original)               # 7 grupos de 5 bits
symbols = map_symbols(groups)                   # 7 pares (x, y)"""
nPad,t, x, y,symbols, S = modulacao32QAM(bits)

x_hat, y_hat = demodulate(S)
groups_rx = decide(x_hat, y_hat)
bits_rx = parallel_to_serial(groups_rx, n_pad)

print("x_hat:", np.round(x_hat, 3))
print("y_hat:", np.round(y_hat, 3))
print("Original:", bits_original)
print("Recebido:", bits_rx)
print("OK?     :", bits_rx == bits_original)


plot_signals(t, x, y, S, n_symbols=len(bits))

