FLAG = "01111110"

# ---------------- Transmissor ----------------
def bit_stuff(payload):
    """Insere um '0' após cada 5 uns consecutivos."""
    out, ones = [], 0
    for b in payload:
        out.append(b)
        if b == "1":
            ones += 1
            if ones == 5:
                out.append("0")      # bit inserido
                ones = 0
        else:
            ones = 0
    return "".join(out)

def build_frame(payload):
    """Encapsula um payload em um quadro: FLAG + payload com stuffing + FLAG."""
    return FLAG + bit_stuff(payload) + FLAG

def frame_message(bits, max_payload=64):
    """Fragmenta a mensagem em payloads de até max_payload bits e gera o fluxo de quadros."""
    frames = [build_frame(bits[k:k + max_payload])
              for k in range(0, len(bits), max_payload)]
    return "".join(frames)

# ---------------- Receptor ----------------
def extract_frames(stream):
    """Varre o fluxo de bits e devolve a lista de payloads (já sem stuffing)."""
    payloads = []
    buf = []            # bits acumulados do quadro atual
    ones = 0            # quantidade de 1s consecutivos
    in_frame = False    # True depois de ver a primeira flag

    for b in stream:
        if b == "1":
            ones += 1
            buf.append("1")
            if ones >= 7:                 # 7 uns seguidos: erro/abort
                buf, ones, in_frame = [], 0, False
        else:  # b == "0"
            if ones == 5:                 # '0' inserido pelo stuffing: descarta
                ones = 0
            elif ones == 6:               # 0 + 111111 + 0 = flag
                if in_frame and len(buf) > 7:
                    payloads.append("".join(buf[:-7]))   # tira o 0 inicial e os 6 uns da flag
                buf, ones, in_frame = [], 0, True        # começa um novo quadro
            else:                         # '0' normal
                buf.append("0")
                ones = 0
    return payloads

def deframe_message(stream):
    return "".join(extract_frames(stream))

# ---------------- Teste ----------------
msg = "0000010011111100100100010111010" + "1111111111" + "01111110"
tx = frame_message(msg, max_payload=16)
rx = deframe_message(tx)

print("Fluxo transmitido:", tx)
print("Mensagem original:", msg)
print("Mensagem recebida:", rx)
print("OK?:", rx == msg)

# Verificação do stuffing
print(bit_stuff("0111111011111"))   # -> 01111101011111 0? veja a saída
assert "111111" not in bit_stuff("1" * 40)