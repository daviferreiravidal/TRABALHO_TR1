"""
Ferramentas comuns aos moduladores: tratam o sinal JÁ CODIFICADO em banda base.

O codificador (NRZ polar, Manchester ou Bipolar) entrega uma lista de "chips":
um valor por intervalo de sinalização, sempre um dos níveis do código
multiplicado por V. Exemplos com V = 1:
    NRZ polar  "101" -> [ 1, -1,  1]          níveis (-1, +1)
    Bipolar    "101" -> [ 1,  0, -1]          níveis (-1, 0, +1)
    Manchester "10"  -> [ 1, -1, -1,  1]      níveis (-1, +1), 2 chips por bit

Os moduladores trabalham com o ÍNDICE de cada nível no alfabeto do código:
    NRZ/Manchester: -V -> 0, +V -> 1               (2 símbolos)
    Bipolar:        -V -> 0,  0 -> 1, +V -> 2      (3 símbolos)
"""
import math


def indice(valor, V, niveis):
    """Índice do nível do alfabeto mais próximo de 'valor' (decisão por distância)."""
    x = valor / V
    return min(range(len(niveis)), key=lambda k: abs(x - niveis[k]))


def para_indices(sinal, V, niveis):
    return [indice(v, V, niveis) for v in sinal]


def para_sinal(indices, V, niveis):
    return [niveis[k] * V for k in indices]


def bits_por_chip(niveis):
    """Quantos bits são necessários para numerar os níveis (2 níveis -> 1, 3 níveis -> 2)."""
    return max(1, math.ceil(math.log2(len(niveis))))


def chips_para_bits(sinal, V, niveis):
    """Usado por 8-PSK e 32-QAM, que agrupam bits em símbolos:
    cada chip vira o número do seu nível escrito em binário."""
    b = bits_por_chip(niveis)
    return "".join(format(k, f"0{b}b") for k in para_indices(sinal, V, niveis))


def bits_para_chips(bits, V, niveis):
    """Inverso de chips_para_bits. Um número que não existe no alfabeto
    (ex.: '11' no bipolar, que só usa 00, 01 e 10) vira o maior nível."""
    b = bits_por_chip(niveis)
    indices = [min(int(bits[i:i + b], 2), len(niveis) - 1)
               for i in range(0, len(bits) - b + 1, b)]
    return para_sinal(indices, V, niveis)
