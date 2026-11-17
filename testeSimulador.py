"""
Casos de teste: mensagens de texto transmitidas pela pilha completa

    texto -> bits -> fragmentação + EDC + enquadramento
          -> codificação banda base / modulação -> + ruído AWGN
          -> demodulação -> desenquadramento -> EDC -> bits -> texto

Rode com:  python testes_fisica.py
"""

from simulador import (
    ENQUADRAMENTOS, EDCS, CODIFICACOES, MODULACOES,
    simular_transmissao, simular_recepcao,
    texto_para_bits, bits_para_texto, montar_mensagem,
)

TAM_QUADRO = 128
TEXTO = "Olá, camada física!"

# (rótulo, argumentos da camada física) para os 7 esquemas
ESQUEMAS = [(c, {"codificacao": c}) for c in CODIFICACOES] + \
           [(m, {"modulacao": m}) for m in MODULACOES]

# tamEdc por tipo de EDC (crc é fixo em 32; hamming ignora)
TAM_EDC = {"checksum": 8, "crc": 32, "hamming": None}

# Ruído "seguro" por esquema (a mensagem tem que chegar íntegra)
SIGMA_SEGURO = {"nrz_polar": 0.1, "bipolar": 0.1, "manchester": 0.5,
                "ASK": 0.5, "FSK": 0.5, "8PSK": 0.5, "32QAM": 0.5}

# Ruídos crescentes para a varredura (o último deve derrubar quadros)
SIGMAS_VARREDURA = {
    "nrz_polar": [0.1, 0.3, 0.5, 1.0],
    "bipolar":   [0.1, 0.2, 0.3, 0.5],
    "manchester": [1, 2, 4, 8],
    "ASK":       [0.5, 1, 2, 4],
    "FSK":       [0.5, 1, 2, 4],
    "8PSK":      [1, 2, 3, 4],
    "32QAM":     [2, 4, 6, 8],
}


def transmitir_texto(texto, enq, edc, fisica, sigma, semente=None):
    """Roda a pilha inteira e devolve (texto_recebido, resultados, sinais)."""
    bits = texto_para_bits(texto)
    k = TAM_EDC[edc]
    sinais = simular_transmissao(bits, TAM_QUADRO, k, enq, edc,
                                 sigma=sigma, semente=semente, **fisica)
    resultados = simular_recepcao(sinais, k, enq, edc, **fisica)
    recebido = bits_para_texto(montar_mensagem(resultados, len(bits)))
    return recebido, resultados, sinais


# --------------------------------------------------------------------------
def teste_1_todas_as_combinacoes():
    """2 enquadramentos x 3 EDCs x 7 esquemas físicos, com ruído seguro."""
    print("=" * 78)
    print(f'TESTE 1: "{TEXTO}" em todas as combinações (ruído AWGN baixo)')
    print("=" * 78)
    nomes = [nome for nome, _ in ESQUEMAS]
    print(f"{'':20s}" + "".join(f"{n:>11s}" for n in nomes))

    houve_padding = False
    for enq in ENQUADRAMENTOS:
        for edc in EDCS:
            linha = f"{enq + ' + ' + edc:20s}"
            for nome, fisica in ESQUEMAS:
                recebido, res, sinais = transmitir_texto(
                    TEXTO, enq, edc, fisica, SIGMA_SEGURO[nome], semente=42)
                ok = recebido == TEXTO and all(r["ok"] for r in res)
                linha += f"{'OK' if ok else 'FALHOU':>11s}"
                houve_padding |= any(s["n_pad"] for s in sinais)
                assert ok, f"{enq}+{edc}+{nome}: recebido={recebido!r}"
            print(linha)
    assert houve_padding, "nenhum caso exercitou o padding do 8PSK/32QAM"
    print("-> todas as 42 combinações entregaram o texto íntegro.\n")


# --------------------------------------------------------------------------
def teste_2_varredura_de_ruido():
    """Quadros reprovados pelo CRC conforme o ruído aumenta."""
    print("=" * 78)
    print("TESTE 2: quadros reprovados pelo CRC x ruído (insercao + crc, 5 rodadas)")
    print("=" * 78)
    for nome, fisica in ESQUEMAS:
        sigmas = [0] + SIGMAS_VARREDURA[nome]
        colunas = []
        for s in sigmas:
            total = ruins = 0
            for rodada in range(5):
                _, res, _ = transmitir_texto(TEXTO, "insercao", "crc", fisica,
                                             s, semente=1000 * rodada)
                total += len(res)
                ruins += sum(not r["ok"] for r in res)
            colunas.append((s, ruins, total))

        assert colunas[0][1] == 0, f"{nome}: falhou sem ruído"
        assert colunas[-1][1] > 0, f"{nome}: ruído máximo não derrubou nenhum quadro"
        print(f"{nome:11s} " + "  ".join(f"s={s}: {r}/{t}" for s, r, t in colunas))
    print("-> sem ruído nada falha; no ruído máximo o CRC reprova quadros.")
    print("   Esquemas que integram muitas amostras por bit/símbolo (Manchester,")
    print("   ASK, FSK, PSK, QAM) aguentam bem mais ruído que NRZ e bipolar.\n")


# --------------------------------------------------------------------------
def teste_3_edc_no_limiar_do_ruido():
    """No limiar de ruído do NRZ polar: detectar x corrigir."""
    print("=" * 78)
    print("TESTE 3: mensagem íntegra em 40 rodadas (contagem, nrz_polar, sigma=0.35)")
    print("=" * 78)
    rodadas = 40
    integras = {}
    for edc in EDCS:
        n = 0
        for rodada in range(rodadas):
            recebido, _, _ = transmitir_texto(
                TEXTO, "contagem", edc, {"codificacao": "nrz_polar"},
                0.35, semente=100 * rodada)
            n += recebido == TEXTO
        integras[edc] = n
        print(f"{edc:9s}: {n}/{rodadas}")
    assert integras["hamming"] > integras["crc"]
    print("-> CRC e checksum só DETECTAM o erro (sem retransmissão a mensagem se")
    print("   perde); o Hamming CORRIGE 1 bit por quadro e entrega mais mensagens.\n")


# --------------------------------------------------------------------------
def teste_4_exemplo_detalhado():
    """Uma transmissão completa, com o resumo de cada quadro."""
    print("=" * 78)
    print('TESTE 4: exemplo detalhado - "Oi, mundo!" em Manchester, sigma=1.0')
    print("=" * 78)
    texto = "Oi, mundo!"
    bits = texto_para_bits(texto)
    print(f"texto: {texto!r} -> {len(bits)} bits")

    sinais = simular_transmissao(bits, TAM_QUADRO, 32, "insercao", "crc",
                                 codificacao="manchester", sigma=1.0,
                                 semente=7, verbose=True)
    res = simular_recepcao(sinais, 32, "insercao", "crc", codificacao="manchester")
    recebido = bits_para_texto(montar_mensagem(res, len(bits)))
    print("EDC por quadro:", ["ok" if r["ok"] else "ERRO" for r in res])
    print(f"texto recebido: {recebido!r}")
    assert recebido == texto
    print()


# --------------------------------------------------------------------------
def teste_5_mensagem_em_bits_e_erros_de_uso():
    """Mensagem já em bits (tamanho que força padding) e validação de parâmetros."""
    print("=" * 78)
    print("TESTE 5: mensagem em bits (tamanho 101) e validação de parâmetros")
    print("=" * 78)
    bits = "1" * 40 + "01" * 30 + "1"          # 101 bits, inclui rajada de 1s
    for nome in ("8PSK", "32QAM"):
        sinais = simular_transmissao(bits, 64, 8, "insercao", "checksum",
                                     modulacao=nome, sigma=0.3, semente=3)
        res = simular_recepcao(sinais, 8, "insercao", "checksum", modulacao=nome)
        assert all(r["ok"] for r in res)
        assert montar_mensagem(res, len(bits)) == bits
        print(f"{nome}: {len(sinais)} quadros, n_pad = {[s['n_pad'] for s in sinais]}"
              " -> mensagem íntegra")

    for kwargs in (dict(codificacao="manchester", modulacao="ASK"),   # as duas
                   dict(sigma=1.0),                                    # ruído sem física
                   dict(codificacao="foo")):                           # nome inválido
        try:
            simular_transmissao("1010", 64, 8, "insercao", "checksum", **kwargs)
        except ValueError as e:
            print(f"ValueError esperado {kwargs}: {e}")
        else:
            raise AssertionError(f"deveria falhar: {kwargs}")
    print()


if __name__ == "__main__":
    teste_1_todas_as_combinacoes()
    teste_2_varredura_de_ruido()
    teste_3_edc_no_limiar_do_ruido()
    teste_4_exemplo_detalhado()
    teste_5_mensagem_em_bits_e_erros_de_uso()
    print("TODOS OS TESTES PASSARAM")