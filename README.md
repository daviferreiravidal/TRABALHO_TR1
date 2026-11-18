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

### Cadeia de transmissão

```
texto -> bits -> EDC -> ENQUADRAMENTO -> 1º CODIFICAÇÃO -> 2º MODULAÇÃO -> canal AWGN
                (Nenhum, Paridade,     (Contagem,        (NRZ polar,       (Nenhuma, ASK,
                 Checksum, CRC-32,      Inserção de       Manchester,       FSK, 8-PSK,
                 Hamming)               bytes / de bits,  Bipolar)          32-QAM)
                                        Entrelaçamento)
```

O **entrelaçamento** usa quadros de tamanho fixo (sem FLAG nem cabeçalho): payload+EDC é
escrito numa matriz de 8 colunas linha por linha e enviado coluna por coluna; o receptor,
que sabe o tamanho do quadro pela configuração, corta o fluxo e desfaz a matriz.

Toda modulação funciona com toda codificação: o modulador recebe o sinal **já codificado**
(um nível -V, 0 ou +V por *chip*; Manchester tem 2 chips por bit) e:

| Modulação | Como usa o sinal codificado |
|---|---|
| Nenhuma | cada chip vira 100 amostras do mesmo nível (banda base no canal) |
| ASK | nível -> amplitude: -V→0, 0→V/2, +V→V (bipolar vira ASK de 3 níveis) |
| FSK | nível -> frequência: 2 níveis usam 4 e 8 ciclos/chip; bipolar usa 4, 6 e 8 |
| 8-PSK / 32-QAM | cada chip vira o número do seu nível em binário (1 bit; 2 no bipolar), agrupado de 3 ou 5 bits por símbolo |

Convenção do projeto: **bits são sempre strings** (`"0110"`), na entrada e na saída de todos os módulos.

### Rodar (sempre a partir da raiz do repositório)

```
python teste_simulador.py     # testes
python -m hermes              # interface gráfica
```

Atalhos: **F5** transmite, **Shift+F5** retransmite com o mesmo ruído, **Ctrl+L** limpa,
**Ctrl+1 / Ctrl+2** mostram Transmissor / Receptor, **F1** sobre, **Ctrl+Q** sai.

O ruído σ é por **amostra** e o receptor integra cada chip/símbolo, por isso σ próximo de 1
ainda costuma passar sem erros. O `teste_simulador.py` imprime uma tabela com o maior σ
sem erros para cada par codificação x modulação.

### Instalar GTK 4 no Windows (MSYS2)

1. Instale o MSYS2 (https://www.msys2.org) e abra o terminal **MSYS2 UCRT64**.
2. `pacman -Suy`
3. `pacman -S mingw-w64-ucrt-x86_64-gtk4 mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-gobject mingw-w64-ucrt-x86_64-python-cairo mingw-w64-ucrt-x86_64-python-numpy`
4. Nesse mesmo terminal: `cd /c/Users/<você>/Documents/codigos/TRABALHO_TR1` e `python -m hermes`

No Linux (Ubuntu/Debian): `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-numpy`.
