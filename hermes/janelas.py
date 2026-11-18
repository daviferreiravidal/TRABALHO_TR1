"""Janelas do Hermes: Transmissor e Receptor."""
from gi.repository import Gio, Gtk

import simulador as sim
from . import __versao__
from .widgets import (BarraStatus, Console, ListaQuadros, Osciloscopio, PainelDetalhes,
                      escolhido, lista_suspensa, moldura, rolagem, texto_somente_leitura)

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
