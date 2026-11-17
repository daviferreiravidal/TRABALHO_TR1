# manchester.py

def codificadorManchester(mensagem, V, amostrasPorBit = 100):
    sinalManchester = []
    meio_bit = amostrasPorBit // 2
    
    for bit in mensagem:
        if bit == '1':
            # '1' representado por transição de +V para -V na metade do período
            sinalManchester.extend([V] * meio_bit)
            sinalManchester.extend([-V] * (amostrasPorBit - meio_bit))
        else:
            # '0' representado por transição de -V para +V na metade do período
            sinalManchester.extend([-V] * meio_bit)
            sinalManchester.extend([V] * (amostrasPorBit - meio_bit))
            
    return sinalManchester

def decodificadorManchester(sinal, V, amostrasPorBit = 100):
    mensagem = []
    nBits = len(sinal) // amostrasPorBit # divide o tamanho do sinal e arredonda para baixo
    meio_bit = amostrasPorBit // 2
    
    for i in range(nBits):
        # pega o bloco de amostras correspondente a um único bit
        bloco = sinal[i * amostrasPorBit: (i + 1) * amostrasPorBit]  
        
        # integra (soma) a primeira metade e a segunda metade do sinal
        soma_primeira_metade = sum(bloco[:meio_bit])
        soma_segunda_metade = sum(bloco[meio_bit:])
        
        # A decisão é feita baseada na transição: 
        # Se a energia inicial for maior que a final, foi +V para -V (Bit '1')
        if soma_primeira_metade > soma_segunda_metade:
            mensagem.append('1')
        else:
            mensagem.append('0')
            
    return mensagem