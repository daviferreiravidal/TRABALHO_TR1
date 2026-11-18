"""
Testa o simulador em TODAS as combinações de
enquadramento x EDC x codificação x modulação.

Rode a partir da raiz do repositório:   python teste_simulador.py
"""
import itertools
import time

from simulador import (Config, ENQUADRAMENTOS, EDCS, CODIFICACOES, MODULACOES,
                       transmitir, canal, receber)

TEXTO = "Olá, camada física! ~}{ Teste do Hermes."   # '~' = 0x7E e '}' = 0x7D (FLAG e ESC)
falhas = total = 0
t0 = time.time()

print("1) Sem ruído: a mensagem tem que chegar idêntica em todas as combinações")
for enq, edc, cod, mod in itertools.product(ENQUADRAMENTOS, EDCS, CODIFICACOES, MODULACOES):
    for nbytes in (1, 5):
        total += 1
        cfg = Config(enquadramento=enq, edc=edc, codificacao=cod, modulacao=mod,
                     bytes_por_quadro=nbytes, V=1.5)
        tx = transmitir(TEXTO, cfg)
        rx = receber(canal(tx["sinal"], cfg), tx["n_pad"], cfg)
        if rx["texto"] != TEXTO or any(q["status"] != "ok" for q in rx["quadros"]):
            falhas += 1
            print(f"   FALHOU: {enq} + {edc} + {cod} + {mod} ({nbytes} B/quadro) -> {rx['texto']!r}")
print(f"   {total - falhas} de {total} combinações OK ({time.time() - t0:.0f} s)\n")

print("2) Codificação x modulação: maior σ (de uma lista) sem nenhum quadro perdido")
SIGMAS = (0.1, 0.2, 0.3, 0.5, 0.8, 1.2, 2, 3, 5)
print("   " + " " * 12 + "".join(f"{m[:10]:>12}" for m in MODULACOES))
for cod in CODIFICACOES:
    linha = f"   {cod:<12}"
    for mod in MODULACOES:
        melhor = 0
        for sg in SIGMAS:
            cfg = Config(edc="CRC-32", codificacao=cod, modulacao=mod, sigma=sg, semente=7)
            tx = transmitir(TEXTO, cfg)
            rx = receber(canal(tx["sinal"], cfg), tx["n_pad"], cfg)
            if rx["texto"] != TEXTO:
                break
            melhor = sg
        linha += f"{melhor:>12}"
    print(linha)

raise SystemExit(1 if falhas else 0)
