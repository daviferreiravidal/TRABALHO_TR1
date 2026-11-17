import math as mt
import numpy as np
import matplotlib.pyplot as plt
from codigosBandabase.bipolar import codificadorBipolar,decodificadorBipolar
from codigosBandaPassante.ASK import *
from AWGN import canalAwgn


def potencia_media(sinal, R=1.0):
    """Potência média (W) em uma resistência R."""
    return np.mean(np.asarray(sinal) ** 2) / R


# ---------------- Simulação ----------------
if __name__ == "__main__":
    # Parâmetros
    V = 5            # amplitude (V)
    f = 5            # ciclos de portadora por bit (parâmetro do seu modulador)
    media = 0.0      # média do ruído (V)
    sigma = 1.5      # desvio padrão do ruído (V)
    AMOSTRAS_BIT = 100   # mesmo valor usado dentro de modulacaoASK

    msg = list("11010011101")
    msg_int = [int(c) for c in msg]

    # 1) Codificação de linha
    bip = codificadorBipolar(len(msg), msg, V)

    # 2) Modulação (seu modulador)
    tx = modulacaoASK(msg_int, f, V)

    # 3) Canal: ruído somado ao sinal modulado
    rx = canalAwgn(tx, media=media, sigma=sigma, semente=42)

    print("Mensagem:", "".join(msg))
    print(f"Potência do sinal TX: {potencia_media(tx):.3f} W (R = 1 ohm)")
    print(f"Potência do ruído   : {potencia_media(rx - np.asarray(tx)):.3f} W")

    # Eixos de tempo (unidade: tempo de bit, já que o modulador não usa Hz)
    m = np.repeat(bip, AMOSTRAS_BIT)
    t = np.arange(len(tx)) / AMOSTRAS_BIT

    # Gráficos
    fig, ax = plt.subplots(4, 1, figsize=(12, 8), sharex=True)

    ax[0].plot(t, m, drawstyle="steps-post", color="tab:blue")
    ax[0].set_title("Codificação de linha bipolar (AMI)")
    ax[0].set_ylabel("Tensão (V)")
    ax[0].set_ylim(-V * 1.5, V * 1.5)
    for i, b in enumerate(msg):
        ax[0].text(i + 0.5, V * 1.25, b, ha="center")

    ax[1].plot(t, tx, color="tab:green", linewidth=0.8)
    ax[1].set_title("Sinal modulado (portadora ASK) sem ruído")
    ax[1].set_ylabel("Tensão (V)")

    ax[2].plot(t, rx, color="tab:red", linewidth=0.8)
    ax[2].set_title(f"Sinal modulado com ruído AWGN (média={media} V, σ={sigma} V)")
    ax[2].set_ylabel("Tensão (V)")
    ax[2].set_xlabel("Tempo (em intervalos de bit)")
    print(rx)
    rxb = demodulacaoASK(rx, V, f)
    print(rxb)
    mrx = np.repeat(rxb, AMOSTRAS_BIT)

    ax[3].plot(t, mrx, color="tab:red", linewidth=0.8)
    ax[3].set_title(f"Sinal demodulado com ruído AWGN (média={media} V, σ={sigma} V)")
    ax[3].set_ylabel("Tensão (V)")
    ax[3].set_ylim(-V * 1.5, V * 1.5)
    for i, b in enumerate(rxb):
            ax[3].text(i + 0.5, V * 1.25, b, ha="center")


    for a in ax:
        a.grid(alpha=0.3)
        for i in range(len(msg) + 1):
            a.axvline(i, color="gray", linestyle=":", linewidth=0.5)

    plt.tight_layout()
    plt.show()