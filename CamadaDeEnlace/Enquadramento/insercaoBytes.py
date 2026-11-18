"""
Enquadramento por INSERÇÃO DE BYTES (byte stuffing), como no Tanenbaum.

Cada quadro começa e termina com um byte especial FLAG. Se o próprio dado
contiver um byte igual a FLAG ou a ESC, o transmissor insere um ESC antes dele;
o receptor, ao ver um ESC, descarta-o e aceita o byte seguinte como dado comum.

    dados:   41  7E  42  7D  43
    quadro:  7E  41  7D 7E  42  7D 7D  43  7E
             ^FLAG   ^ESC        ^ESC       ^FLAG

Entradas e saídas são strings de bits ("0110..."), com tamanho múltiplo de 8.
"""

FLAG = "01111110"   # 0x7E
ESC = "01111101"    # 0x7D


def _bytes(bits):
    if len(bits) % 8 != 0:
        raise ValueError("inserção de bytes: o número de bits precisa ser múltiplo de 8")
    return [bits[i:i + 8] for i in range(0, len(bits), 8)]


# ---------------- Transmissor ----------------
def byte_stuff(payload):
    """Insere um ESC antes de cada byte igual a FLAG ou ESC."""
    saida = []
    for byte in _bytes(payload):
        if byte in (FLAG, ESC):
            saida.append(ESC)
        saida.append(byte)
    return "".join(saida)


def build_frame(payload):
    """Encapsula um payload em um quadro: FLAG + payload com stuffing + FLAG."""
    return FLAG + byte_stuff(payload) + FLAG


def frame_message(bits, max_bytes=8):
    """Fragmenta a mensagem em payloads de até max_bytes bytes e gera o fluxo de quadros."""
    passo = 8 * max_bytes
    return "".join(build_frame(bits[k:k + passo]) for k in range(0, len(bits), passo))


# ---------------- Receptor ----------------
def extract_frames(stream):
    """Varre o fluxo byte a byte e devolve a lista de payloads (já sem os ESC).

    Toda FLAG fecha o quadro que estava aberto (se houver algo nele) e abre
    um novo. Assim, "FLAG dados FLAG FLAG dados FLAG" vira dois quadros, e se
    uma FLAG for corrompida pelo ruído o receptor se ressincroniza na próxima.
    Bits que sobram no fim (menos de 1 byte) são ignorados.
    """
    payloads = []
    buf = []
    dentro = False          # já vimos a primeira FLAG?
    escapando = False       # o byte anterior era um ESC?

    for i in range(0, len(stream) - 7, 8):
        byte = stream[i:i + 8]
        if escapando:                       # byte depois do ESC: é dado, seja o que for
            buf.append(byte)
            escapando = False
        elif byte == FLAG:
            if dentro and buf:
                payloads.append("".join(buf))
            buf, dentro = [], True
        elif byte == ESC:
            escapando = True
        elif dentro:
            buf.append(byte)
    return payloads


def deframe_message(stream):
    return "".join(extract_frames(stream))


# ---------------- Teste ----------------
if __name__ == "__main__":
    def b(*hexas):
        return "".join(format(h, "08b") for h in hexas)

    msg = b(0x41, 0x7E, 0x42, 0x7D, 0x43)
    quadro = build_frame(msg)
    print("Quadro:", " ".join(f"{int(quadro[i:i+8], 2):02X}" for i in range(0, len(quadro), 8)))
    print("OK?:", extract_frames(quadro) == [msg])

    longa = b(*range(256))
    print("Ida-volta com todos os bytes 00..FF:", deframe_message(frame_message(longa, 5)) == longa)
