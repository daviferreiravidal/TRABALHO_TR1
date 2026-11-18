"""
Testa o simulador em TODAS as combinações de enquadramento x EDC x camada física.

Rode a partir da raiz do repositório:   python teste_simulador.py
"""
from simulador import Config, ENQUADRAMENTOS, EDCS, FISICAS, transmitir, canal, receber

TEXTO = "Olá, camada física! Teste do simulador de redes."
falhas = 0

print("1) Sem ruído: a mensagem tem que chegar idêntica em todas as combinações")
for enq in ENQUADRAMENTOS:
    for edc in EDCS:
        for fis in FISICAS:
            for nbytes in (1, 3, 8):
                cfg = Config(enquadramento=enq, edc=edc, fisica=fis, bytes_por_quadro=nbytes)
                tx = transmitir(TEXTO, cfg)
                rx = receber(canal(tx["sinal"], cfg), tx["n_pad"], cfg)
                if rx["texto"] != TEXTO or any(q["status"] != "ok" for q in rx["quadros"]):
                    falhas += 1
                    print(f"   FALHOU: {enq} + {edc} + {fis} ({nbytes} bytes/quadro) -> {rx['texto']!r}")
print(f"   {len(ENQUADRAMENTOS) * len(EDCS) * len(FISICAS) * 3 - falhas} combinações OK, {falhas} falhas\n")

print("2) Com ruído forte no NRZ: o EDC tem que perceber os quadros estragados")
for edc in EDCS:
    cfg = Config(edc=edc, fisica="NRZ polar", sigma=0.6)
    tx = transmitir(TEXTO, cfg)
    rx = receber(canal(tx["sinal"], cfg, semente=3), tx["n_pad"], cfg)
    st = [q["status"] for q in rx["quadros"]]
    print(f"   {edc:13s} quadros: " + " ".join(s[0].upper() for s in st)
          + "   (O=ok C=corrigido E=erro T=truncado)")

raise SystemExit(1 if falhas else 0)
