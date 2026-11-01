POLY = 0x04C11DB7
R = 32
MASK = 0xFFFFFFFF

def crc_bits(bits):
    bits_aux = bits + ('0' * R)

    # janela inicial: primeiros 32 bits da mensagem aumentada
    crc = int(bits_aux[:32], 2)

    # traz um bit por vez (um deslocamento por bit restante)
    for b in range(32, len(bits_aux)):
        top = (crc >> 31) & 1                        # bit que vai "transbordar"
        crc = ((crc << 1) | int(bits_aux[b])) & MASK # desloca, traz o próximo bit, limita a 32 bits
        if top:
            crc ^= POLY

    return crc