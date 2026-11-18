"""
INTERFACE GRÁFICA (HERMES) — entrada de dados e resultados gráficos.

Feita com GTK 4 (PyGObject), biblioteca de interface gráfica do Linux/GNOME.
Duas janelas:
    Transmissor ... mensagem, escolha das técnicas de cada camada, sinal
                    codificado e modulado (osciloscópio) e quadros enviados
    Receptor ...... sinal recebido com ruído, banda base recuperada, quadros
                    recebidos (status de cada um), estatísticas e mensagem

Não é executada diretamente: o Simulador.py (rotina principal) chama
executar(simulador), entregando o módulo com as funções de simulação.
"""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

import datetime
import sys
import threading
import time
import traceback

import numpy as np
from gi.repository import Gdk, Gio, GLib, Gtk, Pango

__versao__ = "1.0"

# Módulo Simulador, entregue pela rotina principal em executar().
# A interface não importa o Simulador diretamente para evitar import circular
# (é o Simulador que abre a interface).
sim = None


# ===========================================================================
# Tema visual retrô (CSS do GTK)
# (originalmente em hermes/estilo.py)
# ===========================================================================
# Tema visual "Windows 95 / software de rede dos anos 90" em CSS do GTK 4.

CINZA = "#c0c0c0"

CSS = """
/* ---------- base ---------- */
window, window.background, .hermes {
    background-color: #c0c0c0;
    color: #000000;
    font-family: "Tahoma", "MS Sans Serif", "Verdana", "DejaVu Sans", sans-serif;
    font-size: 9pt;
}
.mono, .mono label, textview.mono, textview.mono text {
    font-family: "Lucida Console", "Courier New", "DejaVu Sans Mono", monospace;
    font-size: 9pt;
}

/* ---------- barra de título azul-marinho ---------- */
headerbar {
    background-image: linear-gradient(to right, #000080, #1084d0);
    background-color: #000080;
    color: #ffffff;
    min-height: 24px;
    padding: 0 3px;
    border: none;
    box-shadow: none;
    border-radius: 0;
}
headerbar .title, headerbar label { color: #ffffff; font-weight: bold; }
headerbar button {
    min-height: 14px; min-width: 16px; padding: 0 1px; margin: 3px 1px;
}
headerbar button image { color: #000000; }

/* ---------- botões em relevo ---------- */
button {
    background-image: none;
    background-color: #c0c0c0;
    color: #000000;
    border-radius: 0;
    border-style: solid;
    border-width: 1px;
    border-color: #ffffff #000000 #000000 #ffffff;
    box-shadow: inset -1px -1px #808080, inset 1px 1px #dfdfdf;
    padding: 3px 12px;
    min-height: 16px;
    text-shadow: none;
    outline: none;
}
button:hover { background-color: #c8c8c8; }
button:active, button:checked {
    border-color: #000000 #ffffff #ffffff #000000;
    box-shadow: inset 1px 1px #808080, inset -1px -1px #dfdfdf;
}
button:disabled, button:disabled label { color: #808080; }
button:focus-visible { outline: 1px dotted #000000; outline-offset: -4px; }

/* ---------- campos afundados ---------- */
entry, spinbutton, dropdown > button, textview.campo, .afundado {
    background-image: none;
    background-color: #ffffff;
    color: #000000;
    border-radius: 0;
    border-style: solid;
    border-width: 1px;
    border-color: #808080 #ffffff #ffffff #808080;
    box-shadow: inset 1px 1px #404040, inset -1px -1px #dfdfdf;
    min-height: 18px;
}
spinbutton > text { background: none; border: none; box-shadow: none; }
spinbutton > button {
    border-width: 1px;
    border-color: #ffffff #000000 #000000 #ffffff;
    box-shadow: inset -1px -1px #808080;
    padding: 0 4px;
    min-height: 0;
    background-color: #c0c0c0;
}
dropdown > button { padding: 1px 4px; }
textview.campo text { background-color: #ffffff; color: #000000; }

/* ---------- molduras ("group box") ---------- */
frame > border {
    border-style: groove;
    border-width: 2px;
    border-color: #ffffff;
    border-radius: 0;
    box-shadow: none;
}
frame > label { margin: 0 4px; font-weight: bold; }

/* ---------- menus ---------- */
popovermenubar {
    background-color: #c0c0c0;
    border-bottom: 1px solid #808080;
    padding: 1px 2px;
}
popovermenubar > item { padding: 2px 8px; border-radius: 0; }
popovermenubar > item:selected { background-color: #000080; color: #ffffff; }
popover > contents, popover.menu > contents {
    background-color: #c0c0c0;
    color: #000000;
    border-radius: 0;
    border-style: solid;
    border-width: 2px;
    border-color: #ffffff #000000 #000000 #ffffff;
    box-shadow: 2px 2px 0 rgba(0,0,0,0.35);
    padding: 2px;
}
popover > arrow { background: none; border: none; }
modelbutton { border-radius: 0; padding: 3px 16px; }
modelbutton:hover, modelbutton:selected { background-color: #000080; color: #ffffff; }
modelbutton accelerator { color: inherit; }

/* ---------- listas (estilo analisador de pacotes) ---------- */
listview, list, .lista {
    background-color: #ffffff;
    color: #000000;
}
list > row { padding: 0 4px; min-height: 16px; border-radius: 0; }
list > row:selected, list > row:selected label { background-color: #000080; color: #ffffff; }
.cabecalho-colunas {
    background-color: #c0c0c0;
    border-style: solid;
    border-width: 1px;
    border-color: #ffffff #000000 #000000 #ffffff;
    padding: 1px 4px;
    font-weight: bold;
}
label.st-ok { color: #006000; }
label.st-corrigido { color: #806000; }
label.st-erro { color: #c00000; }
label.st-truncado, label.st-perdido { color: #800080; }
list > row:selected label.st-ok, list > row:selected label.st-corrigido,
list > row:selected label.st-erro, list > row:selected label.st-truncado { color: #ffffff; }

/* ---------- console verde ---------- */
textview.console, textview.console text {
    background-color: #000000;
    color: #33ff33;
    font-family: "Lucida Console", "Courier New", "DejaVu Sans Mono", monospace;
    font-size: 9pt;
}

/* ---------- barra de status ---------- */
.statusbar { padding: 2px; }
.statusbar > label {
    border-style: solid;
    border-width: 1px;
    border-color: #808080 #ffffff #ffffff #808080;
    padding: 1px 6px;
}

/* ---------- barras de rolagem clássicas ---------- */
scrollbar { background-color: #dfdfdf; }
scrollbar slider {
    background-color: #c0c0c0;
    border-radius: 0;
    border-style: solid;
    border-width: 1px;
    border-color: #ffffff #000000 #000000 #ffffff;
    min-width: 12px;
    min-height: 12px;
}
paned > separator { background-color: #c0c0c0; min-width: 4px; min-height: 4px; }

/* ---------- miscelânea ---------- */
.resultado-ok { color: #006000; font-weight: bold; }
.resultado-falha { color: #c00000; font-weight: bold; }
.contador-excedido { color: #c00000; font-weight: bold; }
.titulo-campo { font-weight: bold; }
"""


def aplicar():
    """Instala o tema na tela inteira (vale para todas as janelas)."""
    provedor = Gtk.CssProvider()
    if hasattr(provedor, "load_from_string"):        # GTK >= 4.12
        provedor.load_from_string(CSS)
    else:
        provedor.load_from_data(CSS, -1)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provedor, Gtk.STYLE_PROVIDER_PRIORITY_USER)


# ===========================================================================
# Componentes: osciloscópio, lista de quadros, detalhes, console
# (originalmente em hermes/widgets.py)
# ===========================================================================
# Componentes visuais reutilizados pelas janelas do Hermes.

# ==========================================================================
# Pequenos atalhos
# ==========================================================================
def moldura(titulo, filho):
    """Group box no estilo Windows 95."""
    f = Gtk.Frame(label=titulo)
    filho.set_margin_top(4)
    filho.set_margin_bottom(4)
    filho.set_margin_start(4)
    filho.set_margin_end(4)
    f.set_child(filho)
    return f


def rolagem(filho, altura_min=0):
    sw = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
    sw.set_overlay_scrolling(False)                 # barras sempre visíveis (clássico)
    if altura_min:
        sw.set_min_content_height(altura_min)
    sw.set_child(filho)
    return sw


def texto_somente_leitura(css="mono"):
    tv = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.CHAR,
                      left_margin=4, right_margin=4, top_margin=2, bottom_margin=2)
    tv.add_css_class(css)
    return tv


def lista_suspensa(opcoes, padrao):
    opcoes = list(opcoes)
    dd = Gtk.DropDown.new_from_strings(opcoes)
    dd.set_selected(opcoes.index(padrao))
    return dd


def escolhido(dropdown):
    return dropdown.get_selected_item().get_string()


class BarraStatus(Gtk.Box):
    """Barra de status com "painéis" afundados, como nos programas antigos."""

    def __init__(self, n_paineis=3):
        super().__init__(spacing=2)
        self.add_css_class("statusbar")
        self.paineis = []
        for i in range(n_paineis):
            lb = Gtk.Label(xalign=0, hexpand=(i == 0), ellipsize=Pango.EllipsizeMode.END)
            self.append(lb)
            self.paineis.append(lb)

    def __setitem__(self, i, texto):
        self.paineis[i].set_label(texto)


# ==========================================================================
# Osciloscópio
# ==========================================================================
class Osciloscopio(Gtk.Box):
    """Tela de osciloscópio de vários canais (fundo preto) com zoom e rolagem.

    Cada canal ocupa uma faixa horizontal da tela e tem sua própria escala.
    Os canais são SINCRONIZADOS no tempo: um canal com menos amostras (por
    exemplo, o sinal codificado, com 1 valor por chip) é esticado para a
    mesma duração do canal mais longo (a portadora, com 100 amostras por chip).

    Quando há mais amostras do que pixels, desenha o "envelope" (mínimo e
    máximo de cada coluna de pixels), como um osciloscópio digital faz.
    """

    VISIVEL_PADRAO = 3000
    CORES = {"verde": (0.2, 1.0, 0.2), "amarelo": (1.0, 0.9, 0.2), "ciano": (0.3, 0.9, 1.0)}

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.canais = []            # lista de dicts: nome, sinal, cor, escala
        self.n = 0                  # tamanho da linha do tempo (canal mais longo)

        self.area = Gtk.DrawingArea(hexpand=True, vexpand=True)
        self.area.set_content_height(230)
        self.area.set_draw_func(self._desenhar)
        self.append(self.area)

        self.ajuste = Gtk.Adjustment(lower=0, upper=1, page_size=1, step_increment=50)
        self.ajuste.connect("value-changed", lambda *_: self.area.queue_draw())

        controles = Gtk.Box(spacing=2)
        for rotulo, dica, fator in (("−", "Afastar (mostra mais amostras)", 2.0),
                                    ("+", "Aproximar (mostra menos amostras)", 0.5)):
            b = Gtk.Button(label=rotulo, tooltip_text=dica)
            b.connect("clicked", lambda _b, f=fator: self.zoom(f))
            controles.append(b)
        tudo = Gtk.Button(label="Tudo", tooltip_text="Mostrar o sinal inteiro")
        tudo.connect("clicked", lambda *_: self._mostrar_trecho(0, self.n))
        controles.append(tudo)
        barra = Gtk.Scrollbar(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.ajuste,
                              hexpand=True)
        controles.append(barra)
        self.append(controles)

    # ---- API ----
    def set_canais(self, canais):
        """canais: lista de (nome, sinal, cor), com cor em Osciloscopio.CORES."""
        self.canais = []
        for nome, sinal, cor in canais:
            sinal = np.asarray(sinal, dtype=float)
            escala = float(np.max(np.abs(sinal))) if sinal.size else 1.0
            self.canais.append({"nome": nome, "sinal": sinal, "cor": self.CORES[cor],
                                "escala": escala or 1.0})
        self.n = max((len(c["sinal"]) for c in self.canais), default=0)
        self._mostrar_trecho(0, min(self.n, self.VISIVEL_PADRAO))

    def limpar(self):
        self.set_canais([])

    def zoom(self, fator):
        if not self.n:
            return
        vis = int(min(max(self.ajuste.get_page_size() * fator, 20), self.n))
        centro = self.ajuste.get_value() + self.ajuste.get_page_size() / 2
        self._mostrar_trecho(int(max(0, min(centro - vis / 2, self.n - vis))), vis)

    # ---- interno ----
    def _mostrar_trecho(self, inicio, visivel):
        n = max(self.n, 1)
        visivel = max(1, visivel)
        self.ajuste.configure(inicio, 0, n, max(visivel // 20, 1), visivel, visivel)
        self.area.queue_draw()

    def _trecho(self, canal, ini, vis):
        """Amostras do canal na janela [ini, ini+vis) da linha do tempo comum."""
        sinal = canal["sinal"]
        if len(sinal) == self.n:
            return sinal[ini:ini + vis]
        idx = np.arange(ini, min(ini + vis, self.n)) * len(sinal) // self.n   # estica no tempo
        return sinal[idx]

    def _desenhar(self, _area, cr, w, h):
        # fundo e retícula 10 x 8
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        cr.set_line_width(1)
        cr.set_source_rgb(0.05, 0.25, 0.05)
        for i in range(1, 10):
            cr.move_to(int(w * i / 10) + 0.5, 0)
            cr.line_to(int(w * i / 10) + 0.5, h)
        for j in range(1, 8):
            cr.move_to(0, int(h * j / 8) + 0.5)
            cr.line_to(w, int(h * j / 8) + 0.5)
        cr.stroke()

        cr.select_font_face("monospace")
        cr.set_font_size(11)

        if not self.canais or self.n == 0:
            cr.set_source_rgb(0.2, 1.0, 0.2)
            cr.move_to(w / 2 - 40, h / 2)
            cr.show_text("SEM SINAL")
            return

        ini = int(self.ajuste.get_value())
        vis = int(self.ajuste.get_page_size())
        rodape_h = 16
        faixa = (h - rodape_h) / len(self.canais)       # altura de cada canal

        for k, canal in enumerate(self.canais):
            y0 = k * faixa
            topo, base = y0 + 20, y0 + faixa - 6
            meio, amp = (topo + base) / 2, (base - topo) / 2

            if k:                                           # separador entre canais
                cr.set_source_rgb(0.15, 0.5, 0.15)
                cr.move_to(0, int(y0) + 0.5)
                cr.line_to(w, int(y0) + 0.5)
                cr.stroke()
            cr.set_source_rgb(0.1, 0.4, 0.1)                # zero volt deste canal
            cr.move_to(0, int(meio) + 0.5)
            cr.line_to(w, int(meio) + 0.5)
            cr.stroke()

            r, g, b = canal["cor"]
            cr.set_source_rgb(r, g, b)
            cr.move_to(6, y0 + 14)
            cr.show_text(f"CH{k + 1}  {canal['nome']}")
            vp = f"Vpico {canal['escala']:.2f}"
            cr.move_to(w - 7 * len(vp) - 6, y0 + 14)
            cr.show_text(vp)

            trecho = self._trecho(canal, ini, vis)
            if len(trecho) == 0:
                continue

            def y(v, meio=meio, amp=amp, esc=canal["escala"]):
                return meio - v / esc * amp

            if len(trecho) > w:                             # envelope min/max por pixel
                cortes = np.linspace(0, len(trecho), int(w) + 1).astype(int)
                mins = np.minimum.reduceat(trecho, cortes[:-1])
                maxs = np.maximum.reduceat(trecho, cortes[:-1])
                cr.set_line_width(1)
                for x in range(int(w)):
                    cr.move_to(x + 0.5, y(maxs[x]))
                    cr.line_to(x + 0.5, y(mins[x]) + 0.5)
            else:                                           # degraus, uma amostra por passo
                dx = w / len(trecho)
                cr.set_line_width(1.5)
                cr.move_to(0, y(trecho[0]))
                for i, v in enumerate(trecho):
                    cr.line_to(i * dx, y(v))
                    cr.line_to((i + 1) * dx, y(v))
            cr.stroke()

        cr.set_source_rgb(0.2, 1.0, 0.2)
        rodape = f"amostras {ini}-{min(ini + vis, self.n) - 1} de {self.n}"
        cr.move_to(w - 7 * len(rodape) - 6, h - 4)
        cr.show_text(rodape)


# ==========================================================================
# Lista de quadros (estilo analisador de pacotes)
# ==========================================================================
class ListaQuadros(Gtk.Box):
    """Tabela simples de texto: cabeçalho fixo + uma linha por quadro."""

    def __init__(self, colunas, ao_selecionar):
        """colunas: lista de (titulo, largura_em_caracteres)."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.colunas = colunas
        self.ao_selecionar = ao_selecionar

        cab = Gtk.Label(label=self._formatar([t for t, _ in colunas]), xalign=0)
        cab.add_css_class("cabecalho-colunas")
        cab.add_css_class("mono")
        self.append(cab)

        self.lista = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.lista.add_css_class("lista")
        self.lista.connect("row-selected", self._selecionou)
        self.append(rolagem(self.lista, 90))

    def _formatar(self, valores):
        partes = []
        for (_, largura), v in zip(self.colunas, valores):
            v = str(v)
            partes.append(v[:largura].ljust(largura) if largura else v)
        return " ".join(partes)

    def limpar(self):
        while (filho := self.lista.get_first_child()) is not None:
            self.lista.remove(filho)

    def preencher(self, linhas):
        """linhas: lista de (valores, status_css)."""
        self.limpar()
        for valores, status in linhas:
            lb = Gtk.Label(label=self._formatar(valores), xalign=0)
            lb.add_css_class("mono")
            if status:
                lb.add_css_class(f"st-{status}")
            self.lista.append(lb)
        primeira = self.lista.get_row_at_index(0)
        if primeira is not None:
            self.lista.select_row(primeira)

    def _selecionou(self, _lista, linha):
        if linha is not None:
            self.ao_selecionar(linha.get_index())


# ==========================================================================
# Painel de detalhes de um quadro (bits coloridos + hex dump)
# ==========================================================================
class PainelDetalhes(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.tv = texto_somente_leitura("mono")
        self.tv.add_css_class("campo")
        b = self.tv.get_buffer()
        b.create_tag("titulo", weight=Pango.Weight.BOLD)
        b.create_tag("rotulo", foreground="#000080", weight=Pango.Weight.BOLD)
        b.create_tag("flag", foreground="#800080", weight=Pango.Weight.BOLD)
        b.create_tag("cabecalho", foreground="#800080", weight=Pango.Weight.BOLD)
        b.create_tag("edc", foreground="#a00000", weight=Pango.Weight.BOLD)
        b.create_tag("enchimento", foreground="#808080")
        b.create_tag("escape", foreground="#ffffff", background="#008080")
        b.create_tag("diferente", background="#ff8080")
        b.create_tag("legenda", foreground="#606060")
        self.append(rolagem(self.tv, 110))

    def limpar(self):
        self.tv.get_buffer().set_text("")

    def _escrever(self, segmentos):
        b = self.tv.get_buffer()
        b.set_text("")
        for texto, *tags in segmentos:
            fim = b.get_end_iter()
            if tags:
                b.insert_with_tags_by_name(fim, texto, *tags)
            else:
                b.insert(fim, texto)

    # ---- decomposição dos campos ----
    @staticmethod
    def _campos_dados(dados, cfg, referencia=None):
        """payload + EDC, com os bits do EDC destacados.
        referencia: os mesmos bits no transmissor, para marcar os que mudaram."""
        n = 8 * cfg.bytes_por_quadro
        if cfg.edc == "Hamming":
            eh_edc = [(i & (i - 1)) == 0 for i in range(1, len(dados) + 1)]
        else:
            eh_edc = [i >= n for i in range(len(dados))]
        segs = []
        for i, bit in enumerate(dados):
            tags = ["edc"] if eh_edc[i] else []
            if referencia is not None and (i >= len(referencia) or referencia[i] != bit):
                tags.append("diferente")
            segs.append((bit, *tags))
        return segs

    @staticmethod
    def _campos_quadro(quadro, cfg):
        if cfg.enquadramento == "Inserção de bytes":
            segs, escapando = [], False
            octetos = [quadro[i:i + 8] for i in range(0, len(quadro), 8)]
            for k, byte in enumerate(octetos):
                if k in (0, len(octetos) - 1):
                    tag = "flag"                                  # FLAG de início/fim
                elif escapando:
                    tag, escapando = None, False                  # dado após ESC
                elif byte == sim.CamadaEnlace.ESC_BYTES:
                    tag, escapando = "escape", True               # ESC inserido
                else:
                    tag = None
                segs.append((byte, tag) if tag else (byte,))
                segs.append((" ",))
            return segs
        if cfg.enquadramento == "Entrelaçamento":
            # uma coluna da matriz por grupo, na ordem em que vai para o canal
            col = sim.CamadaEnlace.NUM_COLUNAS_ENTRELACAMENTO
            linhas = len(quadro) // col
            segs = []
            for c in range(col):
                segs += [(quadro[c * linhas:(c + 1) * linhas], "cabecalho" if c % 2 else "flag"),
                         (" ",)]
            return segs
        if cfg.enquadramento == "Inserção de bits":
            f = len(sim.CamadaEnlace.FLAG_BITS)
            return [(quadro[:f], "flag"), (" ",), (quadro[f:-f],), (" ",), (quadro[-f:], "flag")]
        return [(quadro[:8], "cabecalho"), (" ",), (quadro[8:],)]

    @staticmethod
    def _hexdump(bits):
        dados = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits) // 8 * 8, 8))
        linhas = []
        for off in range(0, len(dados), 8):
            pedaco = dados[off:off + 8]
            hexa = " ".join(f"{x:02x}" for x in pedaco).ljust(8 * 3)
            asc = "".join(chr(x) if 32 <= x < 127 else "." for x in pedaco)
            linhas.append(f"  {off:04x}  {hexa} {asc}\n")
        return "".join(linhas) or "  (vazio)\n"

    @staticmethod
    def _legenda_edc(cfg):
        return {"Hamming": "bits de paridade nas posições 1, 2, 4, 8...",
                "Nenhum": "sem EDC"}.get(cfg.edc, f"{cfg.edc} no final")

    # ---- telas ----
    def mostrar_tx(self, i, q, cfg):
        segs = [(f"Quadro #{i}  —  {cfg.enquadramento} / {cfg.edc}\n\n", "titulo"),
                ("Payload      ", "rotulo"), (f"({len(q['payload'])} bits)\n  ",),
                (q["payload"] + "\n\n",),
                ("Payload+EDC  ", "rotulo"), (f"({len(q['dados'])} bits; ",),
                (self._legenda_edc(cfg), "edc"), (")\n  ",)]
        segs += self._campos_dados(q["dados"], cfg)
        segs += [("\n\n",), ("Quadro       ", "rotulo"), (f"({len(q['quadro'])} bits)\n  ",)]
        segs += self._campos_quadro(q["quadro"], cfg)
        if cfg.enquadramento == "Entrelaçamento":
            segs += self._matriz_entrelacamento(q["dados"])
        segs += [("\n\n",), ("Hex dump do payload\n", "rotulo"), (self._hexdump(q["payload"]),)]
        self._escrever(segs)

    @staticmethod
    def _matriz_entrelacamento(dados):
        """A matriz do entrelaçamento: escrita por linha, lida por coluna."""
        col = sim.CamadaEnlace.NUM_COLUNAS_ENTRELACAMENTO
        dados = dados + "0" * (-len(dados) % col)
        segs = [("\n  (cada grupo é uma coluna da matriz)\n\n", "legenda"),
                ("Matriz         ", "rotulo"),
                (f"({len(dados) // col} linhas x {col} colunas; escrita por linha, "
                 f"lida por coluna)\n", "legenda")]
        for i in range(0, len(dados), col):
            segs.append(("  " + " ".join(dados[i:i + col]) + "\n",))
        return segs

    def mostrar_rx(self, i, q, cfg, q_tx=None):
        status = q["status"].upper()
        segs = [(f"Quadro #{i}  —  ", "titulo"), (f"[{status}]\n\n", "titulo")]
        segs += [("Payload+EDC recebido  ", "rotulo"), (f"({len(q['dados'])} bits)\n  ",)]
        ref = q_tx["dados"] if q_tx is not None else None
        segs += self._campos_dados(q["dados"], cfg, ref)
        if ref is not None:
            dif = sim.bits_errados(ref, q["dados"])
            segs += [(f"\n  {dif} bit(s) diferente(s) do quadro #{i} enviado", "legenda"),
                     (" (fundo vermelho)", "diferente") if dif else ("",)]
        descartado = q["status"] not in ("ok", "corrigido")
        segs += [("\n\n",), ("Payload (descartado: não entra na mensagem)\n" if descartado
                              else "Payload entregue\n", "rotulo")]
        if q["payload"] is None:
            segs += [("  (não foi possível extrair)\n",)]
        else:
            segs += [("  " + q["payload"] + "\n\n",), ("Hex dump\n", "rotulo"),
                     (self._hexdump(q["payload"]),)]
        self._escrever(segs)


# ==========================================================================
# Console de log (verde no preto)
# ==========================================================================
class Console(Gtk.Box):
    MAX_LINHAS = 2000

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.tv = texto_somente_leitura("console")
        self.tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        b = self.tv.get_buffer()
        b.create_tag("aviso", foreground="#ffff55")
        b.create_tag("erro", foreground="#ff5555")
        b.create_tag("info", foreground="#55ffff")
        self.append(rolagem(self.tv, 80))

    def log(self, msg, nivel=None):
        b = self.tv.get_buffer()
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        fim = b.get_end_iter()
        texto = f"[{hora}] {msg}\n"
        if nivel:
            b.insert_with_tags_by_name(fim, texto, nivel)
        else:
            b.insert(fim, texto)
        excesso = b.get_line_count() - self.MAX_LINHAS
        if excesso > 0:
            b.delete(b.get_start_iter(), b.get_iter_at_line(excesso)[1])
        self.tv.scroll_to_mark(b.get_insert(), 0, False, 0, 0)
        b.place_cursor(b.get_end_iter())
        self.tv.scroll_to_mark(b.get_insert(), 0, False, 0, 0)

    def bruto(self, texto):
        """Escreve sem carimbo de hora (banner)."""
        b = self.tv.get_buffer()
        b.insert(b.get_end_iter(), texto)

    def limpar(self):
        self.tv.get_buffer().set_text("")


# ===========================================================================
# Janelas Transmissor e Receptor
# (originalmente em hermes/janelas.py)
# ===========================================================================
# Janelas do Hermes: Transmissor e Receptor.

BANNER = r"""
  _   _ _____ ____  __  __ _____ ____
 | | | | ____|  _ \|  \/  | ____/ ___|
 | |_| |  _| | |_) | |\/| |  _| \___ \
 |  _  | |___|  _ <| |  | | |___ ___) |
 |_| |_|_____|_| \_\_|  |_|_____|____/   v{v}
 Simulador de camada física e de enlace
"""


def menu_principal():
    """Barra de menus clássica (Arquivo / Simulação / Janelas / Ajuda)."""
    raiz = Gio.Menu()

    arquivo = Gio.Menu()
    arquivo.append("Limpar tudo", "app.limpar")
    arquivo.append("Sair", "app.sair")
    raiz.append_submenu("Arquivo", arquivo)

    simulacao = Gio.Menu()
    simulacao.append("Transmitir", "app.transmitir")
    simulacao.append("Retransmitir (mesmo ruído)", "app.retransmitir")
    raiz.append_submenu("Simulação", simulacao)

    janelas = Gio.Menu()
    janelas.append("Transmissor", "app.mostrar_tx")
    janelas.append("Receptor", "app.mostrar_rx")
    raiz.append_submenu("Janelas", janelas)

    ajuda = Gio.Menu()
    ajuda.append("Legenda de cores", "app.legenda")
    ajuda.append("Sobre o Hermes", "app.sobre")
    raiz.append_submenu("Ajuda", ajuda)
    return raiz


class JanelaBase(Gtk.ApplicationWindow):
    """Moldura comum: barra de título azul, menus, conteúdo, log e barra de status."""

    def __init__(self, app, titulo, titulo_log):
        super().__init__(application=app, title=f"HERMES - {titulo}")
        self.add_css_class("hermes")
        self.set_default_size(1150, 800)

        barra_titulo = Gtk.HeaderBar()
        barra_titulo.set_title_widget(Gtk.Label(label=f"HERMES - {titulo}"))
        barra_titulo.set_decoration_layout(":minimize,maximize,close")
        self.set_titlebar(barra_titulo)

        self.caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.caixa.append(Gtk.PopoverMenuBar.new_from_model(menu_principal()))
        self.set_child(self.caixa)

        self.conteudo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                                margin_start=6, margin_end=6, vexpand=True)
        self.caixa.append(self.conteudo)

        self.console = Console()
        log = moldura(titulo_log, self.console)
        log.set_margin_start(6)
        log.set_margin_end(6)
        log.set_size_request(-1, 130)
        self.caixa.append(log)

        self.status = BarraStatus(3)
        self.caixa.append(self.status)

    def painel_sinal_e_quadros(self, colunas, ao_selecionar):
        """Lado direito comum: osciloscópio em cima, lista + detalhes embaixo."""
        self.osc = Osciloscopio()
        self.lista = ListaQuadros(colunas, ao_selecionar)
        self.detalhes = PainelDetalhes()

        baixo = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
        baixo.set_start_child(moldura("Quadros", self.lista))
        baixo.set_end_child(moldura("Detalhes do quadro", self.detalhes))
        baixo.set_position(170)

        direita = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
        direita.set_start_child(moldura("Osciloscópio", self.osc))
        direita.set_end_child(baixo)
        direita.set_position(290)
        return direita


# ==========================================================================
# Transmissor
# ==========================================================================
class JanelaTX(JanelaBase):
    COLUNAS = [("No.", 5), ("Bits", 6), ("Payload", 8), ("EDC", 6), ("Dados (ASCII)", 0)]

    def __init__(self, app):
        super().__init__(app, "Transmissor", "Log do transmissor")
        self.app = app
        self.ultimo = None                         # (tx, cfg) da última transmissão
        padrao = sim.Config()

        # ---- formulário ----
        grade = Gtk.Grid(column_spacing=8, row_spacing=6)

        self.msg = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, left_margin=3, top_margin=2)
        self.msg.add_css_class("campo")
        self.msg.get_buffer().set_text("Olá, mundo! Este é o Hermes.")
        self.msg.get_buffer().connect("changed", self._contar_bytes)
        caixa_msg = rolagem(self.msg, 70)
        caixa_msg.set_vexpand(False)
        caixa_msg.add_css_class("afundado")
        self.contador = Gtk.Label(xalign=1)

        self.enq = lista_suspensa(sim.ENQUADRAMENTOS, padrao.enquadramento)
        self.edc = lista_suspensa(sim.EDCS, padrao.edc)
        self.cod = lista_suspensa(sim.CODIFICACOES, padrao.codificacao)
        self.mod = lista_suspensa(sim.MODULACOES, padrao.modulacao)
        self.tam = self._spin(1, sim.MAX_BYTES_QUADRO, 1, 0, padrao.bytes_por_quadro)
        self.sigma = self._spin(0, sim.MAX_SIGMA, 0.05, 2, padrao.sigma)
        self.amp = self._spin(0.1, 10, 0.1, 1, padrao.V)
        self.semente = self._spin(0, 999999, 1, 0, 0)
        self.semente.set_tooltip_text("0 = ruído diferente a cada transmissão")

        linha = 0
        grade.attach(self._rotulo("Mensagem:"), 0, linha, 2, 1); linha += 1
        grade.attach(caixa_msg, 0, linha, 2, 1); linha += 1
        grade.attach(self.contador, 0, linha, 2, 1); linha += 1
        for rotulo, w in (("Enquadramento:", self.enq), ("Detecção/correção:", self.edc),
                          ("Bytes por quadro:", self.tam)):
            grade.attach(self._rotulo(rotulo), 0, linha, 1, 1)
            grade.attach(w, 1, linha, 1, 1)
            linha += 1

        fisica = self._grade((("1º Codificação:", self.cod), ("2º Modulação:", self.mod),
                              ("Amplitude V:", self.amp)))
        canal = self._grade((("Ruído AWGN (σ):", self.sigma), ("Semente:", self.semente)))

        self.botao = Gtk.Button(label="Transmitir  [F5]")
        self.botao.connect("clicked", lambda *_: app.activate_action("transmitir"))
        self.spinner = Gtk.Spinner()
        botoes = Gtk.Box(spacing=6)
        botoes.append(self.botao)
        botoes.append(self.spinner)

        esquerda = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        esquerda.append(moldura("Camada de enlace", grade))
        esquerda.append(moldura("Camada física", fisica))
        esquerda.append(moldura("Canal", canal))
        esquerda.append(botoes)
        esquerda.set_size_request(330, -1)

        principal = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, wide_handle=True,
                              vexpand=True)
        principal.set_start_child(esquerda)
        principal.set_resize_start_child(False)
        principal.set_end_child(self.painel_sinal_e_quadros(self.COLUNAS, self._selecionou))
        self.conteudo.append(principal)

        self._contar_bytes()
        self.console.bruto(BANNER.format(v=__versao__))
        self.console.log("Pronto. Configure o enlace e pressione F5 para transmitir.", "info")
        self.status[0] = "Pronto"
        self.status[1] = "Quadros: -"
        self.status[2] = "Bits no canal: -"

    # ---- auxiliares de formulário ----
    @staticmethod
    def _rotulo(texto):
        return Gtk.Label(label=texto, xalign=0)

    def _grade(self, campos):
        grade = Gtk.Grid(column_spacing=8, row_spacing=6)
        for i, (rotulo, w) in enumerate(campos):
            grade.attach(self._rotulo(rotulo), 0, i, 1, 1)
            grade.attach(w, 1, i, 1, 1)
        return grade

    @staticmethod
    def _spin(minimo, maximo, passo, digitos, valor):
        s = Gtk.SpinButton.new_with_range(minimo, maximo, passo)
        s.set_digits(digitos)
        s.set_value(valor)
        s.set_numeric(True)
        s.set_hexpand(True)
        return s

    def texto(self):
        b = self.msg.get_buffer()
        return b.get_text(b.get_start_iter(), b.get_end_iter(), False)

    def _contar_bytes(self, *_):
        n = len(self.texto().encode("utf-8"))
        self.contador.set_label(f"{n} / {sim.MAX_BYTES_MENSAGEM} bytes")
        if n > sim.MAX_BYTES_MENSAGEM or n == 0:
            self.contador.add_css_class("contador-excedido")
        else:
            self.contador.remove_css_class("contador-excedido")

    def ler_config(self):
        for s in (self.tam, self.sigma, self.amp, self.semente):
            s.update()                               # aceita valor digitado sem Enter
        semente = self.semente.get_value_as_int()
        return sim.Config(enquadramento=escolhido(self.enq), edc=escolhido(self.edc),
                          codificacao=escolhido(self.cod), modulacao=escolhido(self.mod),
                          bytes_por_quadro=self.tam.get_value_as_int(),
                          sigma=round(self.sigma.get_value(), 4), V=self.amp.get_value(),
                          semente=semente or None)

    def ocupado(self, sim_ou_nao):
        self.botao.set_sensitive(not sim_ou_nao)
        if sim_ou_nao:
            self.spinner.start()
            self.status[0] = "Transmitindo..."
        else:
            self.spinner.stop()

    # ---- resultados ----
    def mostrar(self, tx, cfg):
        self.ultimo = (tx, cfg)
        canal2 = ("NO CANAL (sem portadora)" if cfg.modulacao.startswith("Nenhuma")
                  else f"PORTADORA {cfg.modulacao}")
        self.osc.set_canais([(f"CODIFICADO {cfg.codificacao}", tx["codificado"], "amarelo"),
                             (canal2, tx["sinal"], "verde")])
        linhas = []
        for i, q in enumerate(tx["quadros"]):
            asc = sim.bits_para_texto(q["payload"]).replace("\n", " ")
            linhas.append(((i, len(q["quadro"]), len(q["payload"]),
                            len(q["dados"]) - len(q["payload"]), asc), None))
        self.lista.preencher(linhas)
        self.status[0] = "Transmissão concluída"
        self.status[1] = f"Quadros: {len(tx['quadros'])}"
        self.status[2] = (f"Bits: {len(tx['fluxo'])}  |  Chips: {len(tx['codificado'])}  |  "
                          f"Amostras: {len(tx['sinal'])}")

    def _selecionou(self, i):
        if self.ultimo:
            tx, cfg = self.ultimo
            self.detalhes.mostrar_tx(i, tx["quadros"][i], cfg)

    def limpar(self):
        self.ultimo = None
        self.osc.limpar()
        self.lista.limpar()
        self.detalhes.limpar()
        self.status[0] = "Pronto"
        self.status[1] = "Quadros: -"
        self.status[2] = "Bits no canal: -"


# ==========================================================================
# Receptor
# ==========================================================================
class JanelaRX(JanelaBase):
    COLUNAS = [("No.", 5), ("Bits", 6), ("Status", 11), ("Dif.", 5), ("Dados (ASCII)", 0)]
    CAMPOS_ESTAT = [("bits_canal", "Bits no canal"), ("bits_errados", "Bits errados"),
                    ("ber", "BER"), ("enviados", "Quadros enviados"),
                    ("recebidos", "Quadros recebidos"), ("ok", "  OK"),
                    ("corrigidos", "  Corrigidos"), ("erros", "  Com erro"),
                    ("truncados", "  Truncados"), ("perdidos", "  Perdidos"),
                    ("eficiencia", "Eficiência")]

    def __init__(self, app):
        super().__init__(app, "Receptor", "Log do receptor")
        self.set_hide_on_close(True)                 # fechar só esconde (reabre pelo menu)
        self.ultimo = None

        grade = Gtk.Grid(column_spacing=12, row_spacing=3)
        self.valores = {}
        for i, (chave, rotulo) in enumerate(self.CAMPOS_ESTAT):
            grade.attach(Gtk.Label(label=rotulo, xalign=0), 0, i, 1, 1)
            v = Gtk.Label(label="-", xalign=1, hexpand=True)
            v.add_css_class("mono")
            grade.attach(v, 1, i, 1, 1)
            self.valores[chave] = v

        self.resultado = Gtk.Label(label="Aguardando sinal...", xalign=0, wrap=True)
        self.mensagem = texto_somente_leitura("campo")
        self.mensagem.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        caixa_msg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        caixa_msg.append(self.resultado)
        caixa_msg.append(rolagem(self.mensagem, 90))

        esquerda = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        esquerda.append(moldura("Estatísticas", grade))
        esquerda.append(moldura("Mensagem recebida", caixa_msg))
        esquerda.set_size_request(330, -1)

        principal = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, wide_handle=True,
                              vexpand=True)
        principal.set_start_child(esquerda)
        principal.set_resize_start_child(False)
        principal.set_end_child(self.painel_sinal_e_quadros(self.COLUNAS, self._selecionou))
        self.conteudo.append(principal)

        self.console.log("Receptor em escuta.", "info")
        self.status[0] = "Aguardando sinal"
        self.status[1] = "Quadros: -"
        self.status[2] = "BER: -"

    def mostrar(self, tx, rx, sinal, cfg, est):
        self.ultimo = (tx, rx, cfg)
        self.osc.set_canais([(f"RECEBIDO {cfg.modulacao}  σ={cfg.sigma:g}", sinal, "verde"),
                             (f"DEMODULADO {cfg.codificacao}", rx["codificado"], "amarelo")])

        linhas = []
        for i, q in enumerate(rx["quadros"]):
            ref = tx["quadros"][i]["dados"] if i < len(tx["quadros"]) else None
            dif = sim.bits_errados(ref, q["dados"]) if ref is not None else "?"
            asc = sim.bits_para_texto(q["payload"]).replace("\n", " ") if q["payload"] else "-"
            linhas.append(((i, len(q["dados"]), q["status"].upper(), dif, asc), q["status"]))
        self.lista.preencher(linhas)
        if not linhas:
            self.detalhes.limpar()

        for chave, rotulo in self.CAMPOS_ESTAT:
            v = est[chave]
            if chave == "ber":
                txt = f"{v:.2e}" if v else "0"
            elif chave == "eficiencia":
                txt = f"{100 * v:.1f} %"
            else:
                txt = str(v)
            self.valores[chave].set_label(txt)

        self.mensagem.get_buffer().set_text(rx["texto"])
        for c in ("resultado-ok", "resultado-falha"):
            self.resultado.remove_css_class(c)
        if est["mensagem_ok"]:
            self.resultado.set_label("✔ Mensagem recebida sem erros")
            self.resultado.add_css_class("resultado-ok")
        else:
            self.resultado.set_label("✘ Mensagem recebida com diferenças")
            self.resultado.add_css_class("resultado-falha")

        self.status[0] = "Recepção concluída"
        self.status[1] = f"Quadros: {est['recebidos']}/{est['enviados']}"
        self.status[2] = f"BER: {est['ber']:.2e}"

    def _selecionou(self, i):
        if self.ultimo:
            tx, rx, cfg = self.ultimo
            q_tx = tx["quadros"][i] if i < len(tx["quadros"]) else None
            self.detalhes.mostrar_rx(i, rx["quadros"][i], cfg, q_tx)

    def limpar(self):
        self.ultimo = None
        self.osc.limpar()
        self.lista.limpar()
        self.detalhes.limpar()
        for v in self.valores.values():
            v.set_label("-")
        self.mensagem.get_buffer().set_text("")
        self.resultado.set_label("Aguardando sinal...")
        for c in ("resultado-ok", "resultado-falha"):
            self.resultado.remove_css_class(c)
        self.status[0] = "Aguardando sinal"
        self.status[1] = "Quadros: -"
        self.status[2] = "BER: -"


# ===========================================================================
# Aplicação: menus, atalhos e simulação em segundo plano
# (originalmente em hermes/app.py)
# ===========================================================================
# Aplicação Hermes: cria as janelas, os menus/atalhos e roda a simulação numa thread.

LEGENDA = (
    "Detalhes do quadro:\n"
    "  roxo      flags (inserção de bits/bytes) ou cabeçalho (contagem)\n"
    "  roxo/vermelho alternados  colunas da matriz (entrelaçamento)\n"
    "  azul-petróleo  byte ESC inserido (inserção de bytes)\n"
    "  vermelho  bits do EDC (paridade, checksum, CRC ou Hamming)\n"
    "  fundo vermelho  bit que chegou diferente do enviado\n\n"
    "Status no receptor:\n"
    "  OK         EDC conferiu\n"
    "  CORRIGIDO  Hamming achou e trocou 1 bit (com 2+ erros pode 'corrigir' errado)\n"
    "  ERRO       EDC acusou erro; o quadro é descartado\n"
    "  TRUNCADO   quadro menor que o esperado (enquadramento perdeu bits)\n"
    "  Perdidos   quadros enviados que o receptor nem chegou a encontrar"
)


class AppHermes(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="br.unb.tr1.hermes",
                         flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.tx = self.rx = None
        self.trabalhando = False
        self.ultima_semente = None

    # ------------------------------------------------------------------
    def do_startup(self):
        Gtk.Application.do_startup(self)
        aplicar()
        acoes = {
            "transmitir": (lambda *_: self.transmitir(), ["F5", "<Control>Return"]),
            "retransmitir": (lambda *_: self.transmitir(repetir=True), ["<Shift>F5"]),
            "limpar": (lambda *_: self.limpar(), ["<Control>l"]),
            "sair": (lambda *_: self.quit(), ["<Control>q"]),
            "mostrar_tx": (lambda *_: self.tx.present(), ["<Control>1"]),
            "mostrar_rx": (lambda *_: self.rx.present(), ["<Control>2"]),
            "legenda": (lambda *_: self.aviso("Legenda de cores", LEGENDA), []),
            "sobre": (lambda *_: self.sobre(), ["F1"]),
        }
        for nome, (funcao, atalhos) in acoes.items():
            acao = Gio.SimpleAction.new(nome, None)
            acao.connect("activate", funcao)
            self.add_action(acao)
            if atalhos:
                self.set_accels_for_action(f"app.{nome}", atalhos)

    def do_activate(self):
        if self.tx is None:
            self.rx = JanelaRX(self)
            self.tx = JanelaTX(self)
            self.tx.connect("close-request", lambda *_: self.quit() or False)
        self.rx.present()
        self.tx.present()

    # ------------------------------------------------------------------
    def transmitir(self, repetir=False):
        if self.trabalhando:
            return
        texto = self.tx.texto()
        cfg = self.tx.ler_config()
        try:
            sim.validar(texto, cfg)
        except ValueError as e:
            self.tx.console.log(f"Configuração inválida: {e}", "erro")
            self.aviso("Não foi possível transmitir", str(e).capitalize() + ".")
            return

        # semente: a escolhida, a da última vez (retransmitir) ou uma nova aleatória
        if cfg.semente is None:
            if repetir and self.ultima_semente is not None:
                cfg.semente = self.ultima_semente
            else:
                cfg.semente = int(time.time_ns() % 1_000_000_007)
        self.ultima_semente = cfg.semente

        self.trabalhando = True
        self.tx.ocupado(True)
        self.rx.status[0] = "Recebendo..."
        self.tx.console.log(
            f"TX {len(texto.encode('utf-8'))} bytes | {cfg.enquadramento} | {cfg.edc} | "
            f"{cfg.codificacao} + {cfg.modulacao} | {cfg.bytes_por_quadro} B/quadro | σ={cfg.sigma:g} | "
            f"semente={cfg.semente}")
        threading.Thread(target=self._simular, args=(texto, cfg), daemon=True).start()

    def _simular(self, texto, cfg):
        """Roda FORA da thread da interface: não pode tocar em nenhum widget aqui."""
        try:
            t0 = time.perf_counter()
            tx = sim.transmitir(texto, cfg)
            sinal_rx = sim.canal(tx["sinal"], cfg)
            rx = sim.receber(sinal_rx, tx["n_pad"], cfg)
            est = sim.estatisticas(tx, rx)
            dt = time.perf_counter() - t0
            GLib.idle_add(self._concluir, tx, rx, sinal_rx, cfg, est, dt)
        except Exception:                      # qualquer bug vira mensagem, não fecha o app
            GLib.idle_add(self._falhou, traceback.format_exc())

    def _concluir(self, tx, rx, sinal_rx, cfg, est, dt):
        self.trabalhando = False
        self.tx.ocupado(False)
        self.tx.mostrar(tx, cfg)
        self.rx.mostrar(tx, rx, sinal_rx, cfg, est)

        self.tx.console.log(f"{len(tx['quadros'])} quadro(s): {len(tx['fluxo'])} bits -> "
                            f"{len(tx['codificado'])} chips ({cfg.codificacao}) -> "
                            f"{len(tx['sinal'])} amostras ({cfg.modulacao}) ({dt:.2f} s)")
        nivel = None if est["mensagem_ok"] else "aviso"
        self.rx.console.log(
            f"RX {est['recebidos']}/{est['enviados']} quadro(s): ok={est['ok']} "
            f"corrigidos={est['corrigidos']} erro={est['erros']} truncados={est['truncados']} "
            f"perdidos={est['perdidos']} | bits errados no canal={est['bits_errados']} "
            f"(BER {est['ber']:.2e})", nivel)
        if est["mensagem_ok"]:
            self.rx.console.log("Mensagem íntegra.", "info")
        else:
            self.rx.console.log("A mensagem entregue difere da enviada.", "erro")
        return False                           # idle_add: rodar uma vez só

    def _falhou(self, detalhes):
        self.trabalhando = False
        self.tx.ocupado(False)
        self.tx.status[0] = "Falha na simulação"
        self.tx.console.log("Erro interno na simulação:", "erro")
        for linha in detalhes.strip().splitlines()[-4:]:
            self.tx.console.log("  " + linha, "erro")
        self.aviso("Erro interno na simulação", detalhes.strip().splitlines()[-1])
        return False

    # ------------------------------------------------------------------
    def limpar(self):
        self.tx.limpar()
        self.rx.limpar()
        self.tx.console.log("Telas limpas.", "info")

    def aviso(self, titulo, texto):
        janela = self.get_active_window() or self.tx
        if hasattr(Gtk, "AlertDialog"):                   # GTK >= 4.10
            Gtk.AlertDialog(message=titulo, detail=texto).show(janela)
        else:
            d = Gtk.MessageDialog(transient_for=janela, modal=True, text=titulo,
                                  secondary_text=texto, buttons=Gtk.ButtonsType.OK)
            d.connect("response", lambda d, _r: d.destroy())
            d.present()

    def sobre(self):
        Gtk.AboutDialog(
            transient_for=self.get_active_window() or self.tx, modal=True,
            program_name="HERMES", version=__versao__,
            comments="Simulador de camada física e de enlace\nTrabalho de Teleinformática e Redes 1",
            website="https://github.com/daviferreiravidal/TRABALHO_TR1",
            license_type=Gtk.License.UNKNOWN,
        ).present()


# ===========================================================================
# Ponto de entrada (chamado pelo Simulador.py)
# ===========================================================================
def executar(simulador):
    """Abre as janelas do Hermes usando as funções do módulo 'simulador'."""
    global sim
    sim = simulador
    return AppHermes().run(sys.argv[:1])
