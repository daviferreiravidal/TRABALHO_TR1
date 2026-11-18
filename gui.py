"""
Interface gráfica (GTK 4) do simulador: uma janela de TRANSMISSÃO e uma de RECEPÇÃO.

Rode a partir da raiz do repositório:   python gui.py

Toda a lógica de redes está em simulador.py; aqui só tem tela.
"""
import sys

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import simulador as sim

MAX_AMOSTRAS_DESENHO = 4000     # desenha só o começo do sinal (para não travar)


# --------------------------------------------------------------------------
# Peças reutilizadas pelas duas janelas
# --------------------------------------------------------------------------
class GraficoSinal(Gtk.DrawingArea):
    """Desenha um sinal (lista/array de números) como uma linha, com cairo."""

    def __init__(self, titulo):
        super().__init__()
        self.titulo = titulo
        self.sinal = []
        self.set_content_height(160)
        self.set_hexpand(True)
        self.set_draw_func(self._desenhar)

    def mostrar(self, sinal):
        self.sinal = sinal[:MAX_AMOSTRAS_DESENHO]
        self.queue_draw()                       # pede ao GTK para redesenhar

    def _desenhar(self, area, cr, w, h):
        cr.set_source_rgb(1, 1, 1)               # fundo branco
        cr.paint()
        cr.set_source_rgb(0.6, 0.6, 0.6)         # eixo do zero
        cr.move_to(0, h / 2)
        cr.line_to(w, h / 2)
        cr.stroke()
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(6, 14)
        cr.show_text(self.titulo)
        if len(self.sinal) < 2:
            return
        maior = max(abs(min(self.sinal)), abs(max(self.sinal))) or 1
        dx = w / len(self.sinal)
        cr.set_source_rgb(0.1, 0.35, 0.8)
        cr.move_to(0, h / 2 - self.sinal[0] / maior * (h / 2 - 20))
        for i, v in enumerate(self.sinal):      # desenha em degraus (cada amostra dura dx)
            y = h / 2 - v / maior * (h / 2 - 20)
            cr.line_to(i * dx, y)
            cr.line_to((i + 1) * dx, y)
        cr.stroke()


def caixa_de_texto():
    """TextView só de leitura, com fonte monoespaçada e barra de rolagem."""
    tv = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.CHAR)
    rolagem = Gtk.ScrolledWindow(vexpand=True, min_content_height=180)
    rolagem.set_child(tv)
    return tv, rolagem


def escrever(textview, texto):
    textview.get_buffer().set_text(texto)


def lista_suspensa(opcoes, padrao):
    dd = Gtk.DropDown.new_from_strings(list(opcoes))
    dd.set_selected(list(opcoes).index(padrao))
    return dd


def escolhido(dropdown):
    return dropdown.get_selected_item().get_string()


# --------------------------------------------------------------------------
# Janela de recepção
# --------------------------------------------------------------------------
class JanelaRX(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Receptor")
        self.set_default_size(700, 560)

        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                        margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        self.set_child(caixa)

        self.grafico = GraficoSinal("Sinal recebido (com ruído)")
        caixa.append(self.grafico)

        self.resumo = Gtk.Label(label="Aguardando transmissão...", xalign=0, wrap=True)
        caixa.append(self.resumo)

        self.detalhes, rolagem = caixa_de_texto()
        caixa.append(rolagem)

        caixa.append(Gtk.Label(label="Mensagem recebida:", xalign=0))
        self.mensagem = Gtk.Label(xalign=0, selectable=True, wrap=True)
        caixa.append(self.mensagem)

    def receber(self, sinal, n_pad, cfg, tx):
        """Chamado pela janela de transmissão quando o sinal 'chega'."""
        rx = sim.receber(sinal, n_pad, cfg)

        self.grafico.mostrar(sinal)

        contagem = {s: sum(q["status"] == s for q in rx["quadros"])
                    for s in ("ok", "corrigido", "erro", "truncado")}
        self.resumo.set_label(
            f"Bits errados no canal: {sim.bits_errados(tx['fluxo'], rx['fluxo'])} "
            f"de {len(tx['fluxo'])}    |    "
            f"Quadros enviados: {len(tx['quadros'])}, recebidos: {len(rx['quadros'])}  "
            f"(ok {contagem['ok']}, corrigidos {contagem['corrigido']}, "
            f"com erro {contagem['erro']}, truncados {contagem['truncado']})")

        linhas = [f"Fluxo de bits demodulado ({len(rx['fluxo'])} bits):", rx["fluxo"], ""]
        for i, q in enumerate(rx["quadros"]):
            linhas.append(f"Quadro {i}: [{q['status'].upper()}]")
            linhas.append(f"  payload+EDC: {q['dados']}")
            linhas.append(f"  payload    : {q['payload']}")
        escrever(self.detalhes, "\n".join(linhas))
        self.mensagem.set_label(rx["texto"])


# --------------------------------------------------------------------------
# Janela de transmissão
# --------------------------------------------------------------------------
class JanelaTX(Gtk.ApplicationWindow):
    def __init__(self, app, janela_rx):
        super().__init__(application=app, title="Transmissor")
        self.set_default_size(700, 560)
        self.janela_rx = janela_rx
        padrao = sim.Config()

        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                        margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        self.set_child(caixa)

        # ---- formulário de configuração ----
        grade = Gtk.Grid(column_spacing=10, row_spacing=6)
        caixa.append(grade)

        self.entrada = Gtk.Entry(text="Olá, mundo!", hexpand=True)
        self.enq = lista_suspensa(sim.ENQUADRAMENTOS, padrao.enquadramento)
        self.edc = lista_suspensa(sim.EDCS, padrao.edc)
        self.fis = lista_suspensa(sim.FISICAS, padrao.fisica)
        self.tam = Gtk.SpinButton.new_with_range(1, 32, 1)
        self.tam.set_value(padrao.bytes_por_quadro)
        self.sigma = Gtk.SpinButton.new_with_range(0, 5, 0.05)
        self.sigma.set_digits(2)
        self.sigma.set_value(padrao.sigma)

        campos = [("Mensagem", self.entrada),
                  ("Enquadramento", self.enq),
                  ("Detecção/correção", self.edc),
                  ("Camada física", self.fis),
                  ("Bytes por quadro", self.tam),
                  ("Ruído AWGN (σ)", self.sigma)]
        for linha, (rotulo, widget) in enumerate(campos):
            grade.attach(Gtk.Label(label=rotulo, xalign=0), 0, linha, 1, 1)
            grade.attach(widget, 1, linha, 1, 1)

        botao = Gtk.Button(label="Transmitir")
        botao.connect("clicked", self.transmitir)
        self.entrada.connect("activate", self.transmitir)   # Enter também transmite
        caixa.append(botao)

        self.erro = Gtk.Label(xalign=0)
        caixa.append(self.erro)

        # ---- saída ----
        self.grafico = GraficoSinal("Sinal transmitido")
        caixa.append(self.grafico)
        self.detalhes, rolagem = caixa_de_texto()
        caixa.append(rolagem)

    def ler_config(self):
        return sim.Config(enquadramento=escolhido(self.enq),
                          edc=escolhido(self.edc),
                          fisica=escolhido(self.fis),
                          bytes_por_quadro=self.tam.get_value_as_int(),
                          sigma=self.sigma.get_value())

    def transmitir(self, *_):
        cfg = self.ler_config()
        try:
            tx = sim.transmitir(self.entrada.get_text(), cfg)
        except ValueError as e:
            self.erro.set_label(f"Erro: {e}")
            return
        self.erro.set_label("")

        self.grafico.mostrar(tx["sinal"])
        linhas = [f"Mensagem em bits ({len(tx['bits'])} bits):", tx["bits"], ""]
        for i, q in enumerate(tx["quadros"]):
            linhas.append(f"Quadro {i}:")
            linhas.append(f"  payload    : {q['payload']}")
            linhas.append(f"  payload+EDC: {q['dados']}")
            linhas.append(f"  enquadrado : {q['quadro']}")
        linhas += ["", f"Fluxo enviado à camada física ({len(tx['fluxo'])} bits, "
                       f"{len(tx['sinal'])} amostras)"]
        escrever(self.detalhes, "\n".join(linhas))

        # o sinal atravessa o canal e "chega" na outra janela
        recebido = sim.canal(tx["sinal"], cfg)
        self.janela_rx.receber(recebido, tx["n_pad"], cfg, tx)


# --------------------------------------------------------------------------
class AppSimulador(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="br.unb.tr1.simulador")

    def do_activate(self):
        rx = JanelaRX(self)
        tx = JanelaTX(self, rx)
        rx.present()
        tx.present()


if __name__ == "__main__":
    sys.exit(AppSimulador().run(sys.argv))
