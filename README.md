# TRABALHO_TR1

## HERMES — simulador de redes

```
simulador.py          lógica (enlace + física + canal AWGN), sem interface
teste_simulador.py    testa todas as combinações (só precisa de numpy)
hermes/               interface gráfica GTK 4
  __main__.py         ponto de entrada (python -m hermes)
  app.py              aplicação: menus, atalhos, thread da simulação
  janelas.py          janelas Transmissor e Receptor
  widgets.py          osciloscópio, lista de quadros, detalhes, console
  estilo.py           tema retrô (CSS)
```

Convenção do projeto: **bits são sempre strings** (`"0110"`), na entrada e na saída de todos os módulos.

### Rodar (sempre a partir da raiz do repositório)

```
python teste_simulador.py     # testes
python -m hermes              # interface gráfica
```

Atalhos: **F5** transmite, **Shift+F5** retransmite com o mesmo ruído, **Ctrl+L** limpa,
**Ctrl+1 / Ctrl+2** mostram Transmissor / Receptor, **F1** sobre, **Ctrl+Q** sai.

O ruído σ é por **amostra**: esquemas com muitas amostras por bit (Manchester, ASK, FSK,
8-PSK, 32-QAM) integram o ruído e aguentam σ bem maior que NRZ e bipolar (1 amostra por bit).

### Instalar GTK 4 no Windows (MSYS2)

1. Instale o MSYS2 (https://www.msys2.org) e abra o terminal **MSYS2 UCRT64**.
2. `pacman -Suy`
3. `pacman -S mingw-w64-ucrt-x86_64-gtk4 mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-gobject mingw-w64-ucrt-x86_64-python-cairo mingw-w64-ucrt-x86_64-python-numpy`
4. Nesse mesmo terminal: `cd /c/Users/<você>/Documents/codigos/TRABALHO_TR1` e `python -m hermes`

No Linux (Ubuntu/Debian): `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-numpy`.
