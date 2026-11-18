# TRABALHO_TR1

## Simulador

- `simulador.py`: lógica (enlace + física + canal AWGN), sem interface.
- `gui.py`: interface GTK 4 com duas janelas (Transmissor e Receptor).
- `teste_simulador.py`: testa todas as combinações sem ruído e mostra o efeito do ruído nos EDCs.

Convenção do projeto: **bits são sempre strings** (`"0110"`), na entrada e na saída de todos os módulos.

### Rodar (sempre a partir da raiz do repositório)

```
python teste_simulador.py     # testes, só precisa de numpy
python gui.py                 # interface gráfica
```

### Instalar GTK 4 no Windows (MSYS2)

1. Instale o MSYS2 (https://www.msys2.org) e abra o terminal **MSYS2 UCRT64**.
2. `pacman -Suy`
3. `pacman -S mingw-w64-ucrt-x86_64-gtk4 mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-gobject mingw-w64-ucrt-x86_64-python-cairo mingw-w64-ucrt-x86_64-python-numpy`
4. Nesse mesmo terminal: `cd /c/Users/<você>/Documents/codigos/TRABALHO_TR1` e `python gui.py`

No Linux (Ubuntu/Debian): `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-numpy`.
