POLY = 0x04C11DB7
r = 31
    
def Meucrc_bits(bits):
    
    bits_aux = bits + (r * '0')


    crc = int(bits_aux[0:32],2)     # crc recebe os n primeiros bits da mensagem, onde n é o tamanho do gerador
                                        # e transfora a string em um número binário

    print("começo: " + bin(crc))

    for b in range(31,len(bits_aux),1):
        print("etapa: ",b-2)
        top = (crc >> 31) & 1            #top recebe o MSB   
        if top:                         #se for 1 
            crc ^= POLY                 #faz o xor com o gerador
            print("crc ^ POLY = ", bin(crc))
        else:
            crc ^= 0x00000000                 #faz xor com 0
            print("crc ^ 0 = " + bin(crc))

        print("crc << 1 = " + bin(crc))
        if b < (len(bits_aux)-1):
            crc = crc << 1                        #desloca para eliminar o transbordo adicionando um 0 pela esquerda
            if int(bits_aux[b+1]):                #verifica quem é o próximo que vai descer na divisão
                crc = crc | 0x00000001                   #se for um flipa o LSB

        print("fim da etapa crc = " + bin(crc))
            
    return crc              # complemento final
            
"""def crc32_str(bits):
    CRC como string de 32 bits (MSB primeiro, ordem de transmissão).
    return format(crc_bits(bits), "04b")"""


bits  = "10110"

print(hex(Meucrc_bits(bits)))
