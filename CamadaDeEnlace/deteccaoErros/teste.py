POLY = 0xD
R = 4
MASK = 0xF

def crc_transmissor(bits):
    bits_aux = bits + ('0' * R)

    # janela inicial: primeiros 32 bits da mensagem aumentada
    crc = int(bits_aux[:4], 2)

    # traz um bit por vez (um deslocamento por bit restante)
    for b in range(3, len(bits_aux)):
        top = (crc >> 3) & 1                        # bit que vai "transbordar"
        crc = ((crc << 1) | int(bits_aux[b])) & MASK # desloca, traz o próximo bit, limita a 32 bits
        if top:
            crc ^= POLY

    return crc

def crc_receptor(bits):

    rest = int(bits[:4],2)

    for b in range(3, len(bits)):
        top = (rest >> 3) & 1
        rest = ((rest << 1) | int(bits[b])) & MASK
        if top:
            rest ^= POLY

    print(rest)

    if rest == 0:
        return True
    else:
        return False


bits = "100100"
result = crc_transmissor(bits)
print(hex(result))                 # 0x569796c2
print(format(result, '04b'))      # 01010110100101111001011011000010

"""""
#caso bom
print(bits + " + " + format(result, '032b'))
bits = bits + format(result, '032b')

print(bits)

if crc_receptor(bits):
    print("bits sem erro")
else:
    print("bits com erro")

#caso ruim

bits_corrompidos = "00110" + format(result, '032b')

if crc_receptor(bits_corrompidos):
    print("bits sem erro")
else:
    print("bits com erro")"""

