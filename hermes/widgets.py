"""Componentes visuais reutilizados pelas janelas do Hermes."""
import datetime

import numpy as np
from gi.repository import Gtk, Pango

import simulador as sim


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
    """Tela de osciloscópio (fundo preto, traço verde) com zoom e rolagem.

    Quando há mais amostras do que pixels, desenha o "envelope" (mínimo e
    máximo de cada coluna de pixels), como um osciloscópio digital faz.
    """

    VISIVEL_PADRAO = 3000

    def __init__(self, canal="CH1", titulo=""):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.canal, self.titulo = canal, titulo
        self.sinal = np.zeros(0)
        self.escala = 1.0

        self.area = Gtk.DrawingArea(hexpand=True, vexpand=True)
        self.area.set_content_height(170)
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
        tudo.connect("clicked", lambda *_: self._mostrar_trecho(0, len(self.sinal)))
        controles.append(tudo)
        barra = Gtk.Scrollbar(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.ajuste,
                              hexpand=True)
        controles.append(barra)
        self.append(controles)

    # ---- API ----
    def set_sinal(self, sinal):
        self.sinal = np.asarray(sinal, dtype=float)
        self.escala = float(np.max(np.abs(self.sinal))) if self.sinal.size else 1.0
        self.escala = self.escala or 1.0
        self._mostrar_trecho(0, min(len(self.sinal), self.VISIVEL_PADRAO))

    def limpar(self):
        self.set_sinal([])

    def zoom(self, fator):
        n = len(self.sinal)
        if not n:
            return
        vis = int(min(max(self.ajuste.get_page_size() * fator, 20), n))
        centro = self.ajuste.get_value() + self.ajuste.get_page_size() / 2
        self._mostrar_trecho(int(max(0, min(centro - vis / 2, n - vis))), vis)

    # ---- interno ----
    def _mostrar_trecho(self, inicio, visivel):
        n = max(len(self.sinal), 1)
        visivel = max(1, visivel)
        self.ajuste.configure(inicio, 0, n, max(visivel // 20, 1), visivel, visivel)
        self.area.queue_draw()

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
        cr.set_source_rgb(0.1, 0.45, 0.1)
        cr.move_to(0, int(h / 2) + 0.5)
        cr.line_to(w, int(h / 2) + 0.5)
        cr.stroke()

        cr.select_font_face("monospace")
        cr.set_font_size(11)
        cr.set_source_rgb(0.2, 1.0, 0.2)
        cr.move_to(6, 14)
        cr.show_text(f"{self.canal}  {self.titulo}")

        n = len(self.sinal)
        if n == 0:
            cr.move_to(w / 2 - 40, h / 2 - 6)
            cr.show_text("SEM SINAL")
            return

        ini = int(self.ajuste.get_value())
        vis = int(self.ajuste.get_page_size())
        trecho = self.sinal[ini:ini + vis]
        topo, base = 22, h - 22                               # margens para os textos
        meio, amp = (topo + base) / 2, (base - topo) / 2

        def y(v):
            return meio - v / self.escala * amp

        cr.set_source_rgb(0.2, 1.0, 0.2)
        if len(trecho) > w:                                   # envelope min/max por pixel
            cortes = np.linspace(0, len(trecho), int(w) + 1).astype(int)
            mins = np.minimum.reduceat(trecho, cortes[:-1])
            maxs = np.maximum.reduceat(trecho, cortes[:-1])
            for x in range(int(w)):
                cr.move_to(x + 0.5, y(maxs[x]))
                cr.line_to(x + 0.5, y(mins[x]) + 0.5)
            cr.stroke()
        else:                                                 # degraus, uma amostra por passo
            dx = w / len(trecho)
            cr.set_line_width(1.5)
            cr.move_to(0, y(trecho[0]))
            for i, v in enumerate(trecho):
                cr.line_to(i * dx, y(v))
                cr.line_to((i + 1) * dx, y(v))
            cr.stroke()

        cr.set_source_rgb(0.2, 1.0, 0.2)
        rodape = f"amostras {ini}-{ini + len(trecho) - 1} de {n}"
        cr.move_to(w - 7 * len(rodape) - 6, h - 8)
        cr.show_text(rodape)
        topo_txt = f"Vpico {self.escala:.2f}"
        cr.move_to(w - 7 * len(topo_txt) - 6, 14)
        cr.show_text(topo_txt)


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
        if cfg.enquadramento == "Inserção de bits":
            f = len(sim.insercaoBits.FLAG)
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
        segs += [("\n\n",), ("Hex dump do payload\n", "rotulo"), (self._hexdump(q["payload"]),)]
        self._escrever(segs)

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
