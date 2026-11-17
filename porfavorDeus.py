from CamadaFisica import *
from CamadaDeEnlace import *

def _modular(bits, modulacao, frequenciaPortadora, amplitudePortadora, AmostrasPorBit = 100):

    if modulacao == "ASK":
        return ASK.modulacaoASK(bits,frequenciaPortadora)
    if modulacao == "FSK":
        return FSK.modulacaoFSK(amplitudePortadora,frequenciaPortadora,frequenciaPortadora*2,bits,AmostrasPorBit)
    if modulacao == "8PSK":
        return PSK_8.modulacao8PSK(bits,fc = frequenciaPortadora, As = 400)
    if modulacao == "32QAM":
        nPad,t, x, y,symbols, S = QAM_32.modulacao32QAM(bits)
        return nPad,t,x, y,symbols, S

def _demodular(sinais, modulacao,amplitudePortadora = 5, frequenciaPortadora = 4,AmostrasPorBit = 100) :

    if modulacao == "ASK":
        return ASK.demodulacaoASK(sinais,amplitudePortadora, frequenciaPortadora)
    if modulacao == "FSK":
        return FSK.demodulacaoFSK(sinais,amplitudePortadora,frequenciaPortadora,frequenciaPortadora*2,AmostrasPorBit)
    if modulacao == "8PSK":
        return PSK_8.demodulacao8PSK(sinais)
    if modulacao == "32QAM":
        return QAM_32.demodulate(sinais)

def _codificar(bits, codificacao,vcc):

    if codificacao == "nrz_polar":
        return nrz_polar.codificar_nrz_polar(vcc,bits)
    if codificacao == "bipolar":
        return bipolar.codificadorBipolar(len(bits),bits,vcc)
    if codificacao == "manchester":
        return manchester.codificadorManchester(bits, vcc, 100)  # 100 amostras por bit

def _decodificar(sinais, codificacao,vcc):

    if codificacao == "nrz_polar":
        return nrz_polar.decodificar_nrz_polar(vcc,sinais)
    if codificacao == "bipolar":
        return bipolar.decodificadorBipolar(sinais,vcc)
    if codificacao == "manchester":
        return manchester.decodificadorManchester(sinais)

def _enquadrar(bits, enquadramento, tamcarga_util):

    if enquadramento == "insercao":
        return insercaoBits.frame_message(bits)
    if enquadramento == "contagem":
        return contagem_de_caracteres.cc_transmissor(tamcarga_util, bits)
    if enquadramento == "entrelaçamento":
        print("não implementado: enquadramento por entrelaçamento")
        return []

def _desenquadrar(quadro, enquadramento):

    if enquadramento == "insercao":
        return insercaoBits.deframe_message(quadro)
    elif enquadramento == "contagem":
        return contagem_de_caracteres.cc_receptor(quadro)
    elif enquadramento == "entrelaçamento":
        print("não implementado: deenquadramento por entrelaçamento")
        return []

def _edc(bits, edc):

    if edc == "checksum":
        return checksum.checksum_receptor(bits)
    if edc == "crc":
        return crc.crc_transmissor(bits)
    if edc == "hamming":
        codeword = hamming.hammingCode(bits)
        return codeword

def _verificarIntegridade(bits, edc):
    if edc == "checksum":
        return checksum.checksum_transmissor(bits)
    if edc == "crc":
        return crc.crc_transmissor(bits)
    if edc == "hamming":
        word,resultado = hamming.hammingCodeReceptor(bits)
        if resultado != 0:
            print(f"erro no: , {resultado}, bit")
            return []
        return word

def simulador_tx(bits, edc,enquadramento, codificacao, modulacao, tamQuadro, tamEDC,VCC,frequenciaPortadora,media = 0,sigma = 1):

    """Simula a transmissão de um quadro, retornando o sinal transmitido e o
    número de bits de padding (0s adicionados para completar o último byte)."""
    # codifica o quadro
    if enquadramento == "insercao":
        tamCargaUtil = tamQuadro - tamEDC - 16
    elif enquadramento == "contagem":
        tamCargaUtil = tamQuadro - tamEDC - 8

    print(f"tamanho da mensagem: {len(bits)}, tamanho do quadro: {tamQuadro}, tamanho do EDC: {tamEDC}, tamanho da carga útil: {tamCargaUtil}")
    enquadrar = True

    #quebra no tamanho de tamQuadro - tamEDC
    partes = [bits[i:i+tamCargaUtil] for i in range(0, len(bits), tamCargaUtil)]

    for i in range(len(partes)):
        print(f"parte {i}: {partes[i]} (tamanho: {len(partes[i])})")


    while enquadrar:
        # aplica o EDC
        cargaUtil_edc = []
        for i in range(len(partes)):
            cargaUtil_edc.append(_edc(partes[i], edc))

        for i in range(len(cargaUtil_edc)):
            print(f"carga útil + EDC {i}: {"".join(cargaUtil_edc[i])} (tamanho: {len("".join(cargaUtil_edc[i]))})")

        quadros = []

        for i in range(len(cargaUtil_edc)):
            quadros.append(_enquadrar(cargaUtil_edc[i], enquadramento, len(cargaUtil_edc[i])))

        for i in range(len(quadros)):
           # print(f"tamanho do quadro {i}: {len("".join(quadros[i]))}")

            if len("".join(quadros[i])) > tamQuadro:
                print(f"ERRO: quadro {i} com EDC tem tamanho {len("".join(quadros[i]))} > {tamQuadro}")
                print("vamos querbrar mais a mensagem em partes menores")
                partes = [partes[i][j:j+(tamCargaUtil//2)] for i in range(len(partes)) for j in range(0, len(partes[i]), (tamCargaUtil//2))]
                print(f"novas partes: {partes}")

                continue

        enquadrar = False


    for i in range(len(quadros)):
        print(f"quadro {i}: {"".join(quadros[i])} (tamanho: {len("".join(quadros[i]))})")

    quadros_codificados = []
    for i in range(len(quadros)):
        quadros_codificados.append(_codificar("".join(quadros[i]), codificacao,vcc=VCC))

    for i in range(len(quadros_codificados)):
        print(f"quadro codificado {i}: {quadros_codificados[i]} (tamanho: {len(quadros_codificados[i])})")

    
    quadros_modulados = []
    for i in range(len(quadros_codificados)):
        if modulacao == "QAM_32":
            nPad,t, x, y,symbols, S = _modular(quadros_codificados[i], modulacao, frequenciaPortadora, VCC)
            quadros_modulados.append(S)
        else:
            quadros_modulados.append(_modular(quadros_codificados[i], modulacao, frequenciaPortadora, VCC))
            

    """for i in range(len(quadros_modulados)):
        print(f"quadro modulado {i}: (tamanho: {len(quadros_modulados[i])})")"""

    quadros_transmitidos = []

    for i in range(len(quadros_modulados)):
        quadros_transmitidos.append(AWGN.canalAwgn(quadros_modulados[i],media,sigma))

    testeModulacao.plot_signals(t,x,y,quadros_transmitidos)

    return quadros_transmitidos # retorna o sinal transmitido

def _simulador_rx(sinais, edc, enquadramento, codificacao, modulacao, tamQuadro, tamEDC,VCC,frequenciaPortadora):

    #demodulamos o sinal recebido
    quadros_demodulados = []
    for i in range(len(sinais)):
        quadros_demodulados.append(_demodular(sinais[i], modulacao,VCC, frequenciaPortadora))

    for i in range(len(quadros_demodulados)):
        print(f"quadro demodulado {i}: {quadros_demodulados[i]} (tamanho: {len(quadros_demodulados[i])})")

    #decodificamos o sinal demodulado
    quadros_decodificados = []
    for i in range(len(quadros_demodulados)):
        quadros_decodificados.append(_decodificar(quadros_demodulados[i], codificacao,VCC))

    for i in range(len(quadros_demodulados)):
        print(f"quadro decodificado {i}: {"".join(quadros_decodificados[i])} (tamanho: {len(quadros_decodificados[i])})")

    #agora que temos nosso quadro desenquadramos
    cargarUtil_edc = []
    for i in range(len(quadros_decodificados)):
        cargarUtil_edc.append(_desenquadrar("".join(quadros_decodificados[i]),enquadramento))

    for i in range(len(quadros_demodulados)):
        print(f"cargaUtil + edc {i}: {"".join(cargarUtil_edc[i])} (tamanho: {len(cargarUtil_edc[i])})")

    #com a carga util de cada quador em mãos verificamos a integridade

    partes = []
    for i in range(len(cargarUtil_edc)):
        partes.append(_verificarIntegridade(cargarUtil_edc[i],edc))

    for i in range(len(cargarUtil_edc)):
        print(f"partes {i}: {"".join(partes[i])} (tamanho: {len(partes[i])})")

    bits = "".join("".join(payloads) for payloads in partes)

    return bits


if __name__ == "__main__":
    bits = "11010010011101011111010111101101011"

    print("_____________________ transmissão _____________________")
    quadros_transmitidos = simulador_tx(bits, "hamming", "insercao", "bipolar", "QAM_32", 24, 4, 5, 4)
    print("\n")
    print("_____________________ recepção _____________________")
    bits_recebidos =_simulador_rx(quadros_transmitidos, "hamming", "insercao", "bipolar", "QAM_32", 24, 4, 5, 4)

    if bits_recebidos == bits:
        print("transmissão realizada com sucesso!")
    