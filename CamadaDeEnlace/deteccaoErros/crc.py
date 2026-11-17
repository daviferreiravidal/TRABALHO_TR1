POLY = 0x04C11DB7
R = 32
MASK = 0xFFFFFFFF

def crc_transmissor(bits):
    """Calcula o CRC de uma mensagem."""
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

def crc_receptor(bits):
    """Verifica se o CRC de uma mensagem recebida é válido."""
    rest = int(bits[:32],2)

    for b in range(32, len(bits)):
        top = (rest >> 31) & 1
        rest = ((rest << 1) | int(bits[b])) & MASK
        if top:
            rest ^= POLY

    if rest == 0:
        return True
    else:
        return False


if __name__ == "__main__":
    bits = "10110"
    result = crc_transmissor(bits)
    print(hex(result))
    print(format(result, "032b"))

    bits_com_crc = bits + format(result, "032b")
    print("bits sem erro" if crc_receptor(bits_com_crc) else "bits com erro")

    bits_corrompidos = "00110" + format(result, "032b")
    print("bits sem erro" if crc_receptor(bits_corrompidos) else "bits com erro")

