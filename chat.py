import sys
import gi
from integracao import transmitir_mensagem, CONFIG_PADRAO

gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Gdk, GLib, Pango

CSS = """
window.fundo {
    background: #1e1e1e;
}

.cartao {
    background: #ffffff;
    border-radius: 28px;
    overflow: hidden;
}

.balao {
    background: #eee8f4;
    color: #49454f;
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.45);
}

.aviso {
    color: #b3261e;
    font-size: 12px;
    margin-top: 6px;
}

.aviso-ok {
    color: #2e7d32;
    font-size: 12px;
    margin-top: 6px;
}

button.pontos {
    background: none;
    border: none;
    box-shadow: none;
    color: #222222;
    font-size: 22px;
    font-weight: bold;
    padding: 0 6px;
    min-width: 0;
    min-height: 0;
}

separator.linha {
    background: #000000;
    min-height: 1px;
}

entry.campo {
    background: #ffffff;
    color: #000000;
    border: 1px solid #79747e;
    border-radius: 6px;
    box-shadow: none;
    min-height: 38px;
    padding: 0 12px;
}

button.enviar {
    background: #ffffff;
    color: #000000;
    border: 3px solid #000000;
    border-radius: 999px;
    min-width: 32px;
    min-height: 32px;
    padding: 0;
    font-size: 18px;
    font-weight: bold;
    box-shadow: none;
}
"""


class JanelaChat(Gtk.ApplicationWindow):
    def __init__(self, app, nome):
        super().__init__(application=app, title=f"Chat - {nome}")
        self.nome = nome
        self.peer = None  # será definido depois (a outra janela)
        self.config = dict(CONFIG_PADRAO)  # a tela inicial (Home) substitui por a escolhida
        self.set_default_size(620, 500)
        self.add_css_class("fundo")

        # ---- Cartão branco arredondado ----
        cartao = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cartao.add_css_class("cartao")
        for lado in ("top", "bottom", "start", "end"):
            getattr(cartao, f"set_margin_{lado}")(18)
        self.set_child(cartao)

        # ---- Área de mensagens (rolável) ----
        self.mensagens = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.mensagens.set_valign(Gtk.Align.END)  # mensagens ficam coladas embaixo
        self.mensagens.set_margin_top(16)
        self.mensagens.set_margin_bottom(16)
        self.mensagens.set_margin_start(14)
        self.mensagens.set_margin_end(14)

        self.rolagem = Gtk.ScrolledWindow()
        self.rolagem.set_vexpand(True)
        self.rolagem.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.rolagem.set_child(self.mensagens)
        cartao.append(self.rolagem)

        # rola até o fim sempre que o conteúdo crescer
        vadj = self.rolagem.get_vadjustment()
        vadj.connect("changed", self._rolar_para_o_fim)

        # ---- Linha separadora ----
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.add_css_class("linha")
        cartao.append(sep)

        # ---- Barra de entrada ----
        barra = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        barra.set_margin_top(18)
        barra.set_margin_bottom(18)
        barra.set_margin_start(36)
        barra.set_margin_end(36)

        self.entrada = Gtk.Entry(placeholder_text="Digite sua mensagem aqui...")
        self.entrada.set_hexpand(True)
        self.entrada.set_alignment(0.5)  # texto centralizado como no design
        self.entrada.add_css_class("campo")
        self.entrada.connect("activate", self.ao_enviar)
        barra.append(self.entrada)

        botao = Gtk.Button(label="\u2192")  # seta →
        botao.add_css_class("enviar")
        botao.set_valign(Gtk.Align.CENTER)
        botao.connect("clicked", self.ao_enviar)
        barra.append(botao)

        cartao.append(barra)

    # ------------------------------------------------------------
    # Construção dos balões
    # ------------------------------------------------------------
    def _criar_balao(self, texto, aviso=None):
        rotulo = Gtk.Label(label=texto)
        rotulo.set_wrap(True)
        rotulo.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        rotulo.set_max_width_chars(36)
        rotulo.set_xalign(0)
        rotulo.set_selectable(False)

        balao = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        balao.add_css_class("balao")
        balao.set_size_request(180, -1)
        balao.append(rotulo)

        if aviso:  # resultado da simulação: erro detectado, quadro perdido, correção...
            lbl = Gtk.Label(label=aviso)
            lbl.set_wrap(True)
            lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            lbl.set_max_width_chars(36)
            lbl.set_xalign(0)
            ok = all(l.startswith("\u2713") for l in aviso.splitlines())
            lbl.add_css_class("aviso-ok" if ok else "aviso")
            balao.append(lbl)
        return balao

    def _criar_botao_pontos(self, texto, resultado, enviada):
        botao = Gtk.Button(label="\u22ee")  # ⋮
        botao.add_css_class("pontos")
        botao.set_valign(Gtk.Align.CENTER)
        botao.set_tooltip_text("Detalhes da transmissão")
        botao.connect("clicked", self.ao_abrir_detalhes, texto, resultado, enviada)
        return botao

    def adicionar_mensagem(self, texto, enviada, resultado=None):
        """enviada=True -> balão à direita (pontos depois);
        enviada=False -> balão à esquerda (pontos antes).
        resultado: dict de integracao.transmitir_mensagem (detalhes e avisos)."""
        linha = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        # quem envia vê o que digitou; quem recebe vê o que chegou, com o aviso da simulação
        aviso = resultado["aviso"] if (resultado and not enviada) else None
        balao = self._criar_balao(texto, aviso)
        pontos = self._criar_botao_pontos(texto, resultado, enviada)

        if enviada:
            linha.set_halign(Gtk.Align.END)
            linha.append(balao)
            linha.append(pontos)
        else:
            linha.set_halign(Gtk.Align.START)
            linha.append(pontos)
            linha.append(balao)

        self.mensagens.append(linha)

    def _rolar_para_o_fim(self, adj):
        adj.set_value(adj.get_upper() - adj.get_page_size())

    # ------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------
    def ao_enviar(self, _widget):
        texto = self.entrada.get_text().strip()
        if not texto:
            return
        self.entrada.set_text("")

        # Simulação das camadas de enlace e física (config escolhida na tela inicial):
        # texto -> quadros + EDC -> codificação/modulação -> ruído AWGN -> e de volta.
        try:
            resultado = transmitir_mensagem(texto, self.config)
        except Exception as e:  # configuração inválida, etc.
            self.adicionar_mensagem(texto, enviada=True)
            self._avisar("Falha na simulação", f"{type(e).__name__}: {e}")
            return

        self.adicionar_mensagem(texto, enviada=True, resultado=resultado)
        if self.peer is not None:
            # o outro lado recebe o que saiu do receptor, não o texto original
            self.peer.receber(resultado["texto_recebido"], resultado)

    def receber(self, texto, resultado=None):
        """Chamado quando a outra janela envia algo para esta."""
        # se nenhum quadro sobreviveu ao canal, não há texto para mostrar
        self.adicionar_mensagem(texto or "[nada foi recebido]", enviada=False,
                                resultado=resultado)

    def ao_abrir_detalhes(self, _botao, texto, resultado, enviada):
        direcao = "enviada" if enviada else "recebida"
        if resultado is None:
            self._avisar(f"Mensagem {direcao}", "Sem detalhes de transmissão.")
            return
        detalhe = (f"Texto enviado:  {resultado['texto_enviado']}\n"
                   f"Texto recebido: {resultado['texto_recebido']}\n\n"
                   f"{resultado['resumo']}")
        self._avisar(f"Detalhes da transmissão ({direcao})", detalhe)

    def _avisar(self, titulo, detalhe):
        if hasattr(Gtk, "AlertDialog"):
            dialogo = Gtk.AlertDialog()
            dialogo.set_message(titulo)
            dialogo.set_detail(detalhe)
            dialogo.show(self)
        else:
            print(f"[{self.nome}] {titulo}: {detalhe}")


class AppChat(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.exemplo.SimuladorEnlace")

    def do_activate(self):
        self._carregar_css()

        janela_a = JanelaChat(self, "Pessoa A")
        janela_b = JanelaChat(self, "Pessoa B")
        janela_a.peer = janela_b
        janela_b.peer = janela_a

        janela_a.present()
        janela_b.present()

    def _carregar_css(self):
        css = Gtk.CssProvider()
        if hasattr(css, "load_from_string"):  # GTK >= 4.12
            css.load_from_string(CSS)
        else:
            css.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


if __name__ == "__main__":
    sys.exit(AppChat().run(sys.argv))