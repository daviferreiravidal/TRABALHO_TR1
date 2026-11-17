import os
import sys
import math
import importlib

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

PASTA = os.path.dirname(os.path.abspath(__file__))

# Arquivo da imagem do Hermes (PNG com fundo transparente, na mesma pasta)
ARQUIVO_HERMES = os.path.join(PASTA, "hermes.png")
# Recorte (x, y, largura, altura) para tirar a margem vazia do PNG original
CORTE_HERMES = (66, 40, 418, 526)

# Nome do módulo (arquivo .py, sem a extensão) com a tela de chat.
# Se o seu arquivo do chat se chama teste.py, troque para "teste".
MODULO_CHAT = "chat"

# Caracteres aceitos em cada tipo de campo numérico
PERMITIDOS = {
    "inteiro": "0123456789",
    "decimal": "0123456789.,",
    "decimal_sinal": "0123456789.,-",
}

CSS = """
window.hermes {
    background: #ffffff;
}

/* ---------- Cabeçalho ---------- */
window.hermes label.titulo {
    font-family: "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
    color: #1c1c1c;
}
window.hermes label.subtitulo {
    color: #6b6b6b;
    font-size: 15px;
    font-style: italic;
}

/* ---------- Seções ---------- */
.painel {
    background: #ffffff;
    border: 1px solid #d6d6d6;
    border-radius: 10px;
    padding: 12px 18px 10px 18px;
}
window.hermes label.titulo-painel {
    font-weight: bold;
    font-size: 14px;
    color: #2b2b2b;
}
window.hermes label.rotulo {
    font-size: 14px;
    color: #2b2b2b;
}
window.hermes label.unidade {
    font-size: 14px;
    color: #6b6b6b;
}

/* ---------- Campos de texto ---------- */
entry.campo-num {
    background: #ffffff;
    color: #222222;
    border: 1px solid #bdbdbd;
    border-radius: 6px;
    box-shadow: none;
    min-height: 30px;
    padding: 0 8px;
}
entry.campo-num:focus-within {
    border-color: #b3261e;
}
entry.campo-num.erro {
    border-color: #c4260f;
    background: #fdecea;
}

/* ---------- Radio buttons ---------- */
window.hermes checkbutton {
    color: #2b2b2b;
    font-size: 14px;
}
window.hermes checkbutton radio {
    min-width: 18px;
    min-height: 18px;
    border: 2px solid #8a8a8a;
    background-color: transparent;
    background-image: none;
    border-radius: 999px;
    box-shadow: none;
    -gtk-icon-source: none;
}
window.hermes checkbutton:hover radio {
    border-color: #b3261e;
}
window.hermes checkbutton radio:checked {
    background-color: #b3261e;
    border-color: #b3261e;
    box-shadow: inset 0 0 0 3px #ffffff;
    -gtk-icon-source: none;
}

/* ---------- Botão principal ---------- */
button.comecar {
    background: #b3261e;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 44px;
    font-size: 17px;
    font-weight: bold;
    box-shadow: none;
}
button.comecar:hover {
    background: #c9342b;
}
button.comecar:active {
    background: #8f1d17;
}
"""


# ----------------------------------------------------------------------
# Componentes
# ----------------------------------------------------------------------
def criar_painel(titulo=None):
    """Caixa com borda fina e (opcionalmente) um título em negrito."""
    caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    caixa.add_css_class("painel")
    if titulo:
        lbl = Gtk.Label(label=titulo)
        lbl.add_css_class("titulo-painel")
        lbl.set_halign(Gtk.Align.START)
        caixa.append(lbl)
    return caixa


def criar_painel_opcoes(titulo, opcoes, colunas=2, homogeneo=True):
    """Painel com radio buttons.

    opcoes: lista de (chave, texto). Preenche coluna por coluna.
    Retorna (widget, {chave: radio}).
    """
    caixa = criar_painel(titulo)

    grade = Gtk.Grid(column_spacing=40, row_spacing=2, column_homogeneous=homogeneo)
    grade.set_hexpand(True)
    caixa.append(grade)

    linhas = math.ceil(len(opcoes) / colunas)
    botoes = {}
    primeiro = None
    for i, (chave, texto) in enumerate(opcoes):
        b = Gtk.CheckButton(label=texto)
        b.set_halign(Gtk.Align.START)
        if primeiro is None:
            primeiro = b
            b.set_active(True)
        else:
            b.set_group(primeiro)
        col, lin = divmod(i, linhas)
        grade.attach(b, col, lin, 1, 1)
        botoes[chave] = b

    return caixa, botoes


def selecionado(botoes):
    for chave, b in botoes.items():
        if b.get_active():
            return chave
    return None


def criar_campo(rotulo, unidade=None, tipo="inteiro", largura=8, dica=None):
    """Rótulo + entrada de texto (+ unidade). Retorna (box, entry)."""
    caixa = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

    lbl = Gtk.Label(label=rotulo)
    lbl.add_css_class("rotulo")
    caixa.append(lbl)

    entrada = Gtk.Entry()
    entrada.add_css_class("campo-num")
    entrada.set_width_chars(largura)
    entrada.set_max_length(12)
    entrada.set_alignment(0.5)
    entrada.set_valign(Gtk.Align.CENTER)
    if dica:
        entrada.set_placeholder_text(dica)
    if tipo == "inteiro":
        entrada.set_input_purpose(Gtk.InputPurpose.DIGITS)
    else:
        entrada.set_input_purpose(Gtk.InputPurpose.NUMBER)

    permitidos = PERMITIDOS[tipo]

    def ao_mudar(e):
        e.remove_css_class("erro")
        texto = e.get_text()
        limpo = "".join(c for c in texto if c in permitidos)
        if limpo != texto:  # remove caracteres inválidos (digitados ou colados)
            pos = e.get_position()
            e.handler_block(id_sinal)
            e.set_text(limpo)
            e.handler_unblock(id_sinal)
            e.set_position(max(0, pos - (len(texto) - len(limpo))))

    id_sinal = entrada.connect("changed", ao_mudar)
    caixa.append(entrada)

    if unidade:
        un = Gtk.Label(label=unidade)
        un.add_css_class("unidade")
        caixa.append(un)

    return caixa, entrada


def criar_linha(*widgets, espaco=36):
    linha = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=espaco)
    for w in widgets:
        linha.append(w)
    return linha


def ler_numero(entrada, inteiro=False, minimo=None, estrito=False, obrigatorio=True):
    """Lê e valida um campo. Retorna (valor, ok). Marca o campo se houver erro."""
    texto = entrada.get_text().strip().replace(",", ".")
    if texto == "":
        if obrigatorio:
            entrada.add_css_class("erro")
            return None, False
        return None, True
    try:
        valor = int(texto) if inteiro else float(texto)
    except ValueError:
        entrada.add_css_class("erro")
        return None, False
    if minimo is not None:
        invalido = valor <= minimo if estrito else valor < minimo
        if invalido:
            entrada.add_css_class("erro")
            return None, False
    return valor, True


# ----------------------------------------------------------------------
# Janela
# ----------------------------------------------------------------------
class JanelaHome(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app,
                         title="Hermes - Simulador de Camadas de Enlace e Modulação")
        self.set_default_size(1200, 940)
        self.add_css_class("hermes")

        raiz = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for lado in ("top", "bottom", "start", "end"):
            getattr(raiz, f"set_margin_{lado}")(20)
        self.set_child(raiz)

        raiz.append(self._criar_cabecalho())

        corpo = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        corpo.set_vexpand(True)
        raiz.append(corpo)

        corpo.append(self._criar_hermes())
        corpo.append(self._criar_coluna_config())

    # ---------------- cabeçalho ----------------
    def _criar_cabecalho(self):
        cab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cab.set_halign(Gtk.Align.CENTER)

        titulo = Gtk.Label()
        titulo.set_markup(
            '<span size="52224" weight="bold">H</span>'
            '<span size="38912" weight="bold">ERMES</span>'
        )
        titulo.add_css_class("titulo")

        subtitulo = Gtk.Label(label="Simulador de Camadas de Enlace e Modulação")
        subtitulo.add_css_class("subtitulo")

        cab.append(titulo)
        cab.append(subtitulo)
        return cab

    # ---------------- imagem ----------------
    def _criar_hermes(self):
        pic = Gtk.Picture()
        pic.set_content_fit(Gtk.ContentFit.CONTAIN)
        pic.set_can_shrink(True)
        pic.set_size_request(400, -1)
        pic.set_hexpand(False)
        pic.set_vexpand(True)
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file(ARQUIVO_HERMES)
            x, y, w, h = CORTE_HERMES
            pb = pb.new_subpixbuf(x, y, w, h)
            pic.set_paintable(Gdk.Texture.new_for_pixbuf(pb))
        except Exception:
            try:
                pic.set_filename(ARQUIVO_HERMES)
            except Exception as e:
                print("Não foi possível carregar hermes.png:", e)
        return pic

    # ---------------- coluna de configuração ----------------
    def _criar_coluna_config(self):
        paineis = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        paineis.set_margin_end(12)

        painel = criar_painel("Tamanho dos quadros e EDC")
        c1, self.entrada_quadro = criar_campo("Tamanho máximo do quadro:", "bits", "inteiro", 7)
        c2, self.entrada_edc = criar_campo("Tamanho do EDC (Checksum):", "bits", "inteiro", 7)
        self.entrada_quadro.set_text("1024")
        self.entrada_edc.set_text("16")
        painel.append(criar_linha(c1, c2, espaco=28))
        dica = Gtk.Label(label="CRC utiliza 32 bits fixos; Hamming calcula o tamanho automaticamente. O campo de EDC é utilizado somente no Checksum.")
        dica.set_wrap(True)
        dica.set_xalign(0)
        dica.add_css_class("unidade")
        painel.append(dica)
        paineis.append(painel)

        p, self.r_enquadramento = criar_painel_opcoes(
            "Método de enquadramento",
            [("contagem", "Contagem de caracteres"),
             ("insercao", "Enquadramento com flags e inserção de bits")],
            colunas=2, homogeneo=False)
        paineis.append(p)

        p, self.r_edc = criar_painel_opcoes(
            "Detecção/correção de erros (EDC)",
            [("checksum", "Checksum"), ("crc", "CRC-32"), ("hamming", "Código de Hamming")],
            colunas=3, homogeneo=False)
        paineis.append(p)

        p, self.r_fisica = criar_painel_opcoes(
            "Camada física: escolha uma opção",
            [("nrz_polar", "Banda-base: NRZ-Polar"),
             ("bipolar", "Banda-base: Bipolar"),
             ("manchester", "Banda-base: Manchester"),
             ("ASK", "Modulação: ASK"), ("FSK", "Modulação: FSK"),
             ("8PSK", "Modulação: 8PSK"), ("32QAM", "Modulação: 32-QAM")],
            colunas=2, homogeneo=False)
        paineis.append(p)

        painel = criar_painel("Parâmetros do sinal")
        c1, self.entrada_voltagem = criar_campo("Amplitude:", "V", "decimal", 7)
        self.entrada_voltagem.set_text("1.0")
        painel.append(c1)
        paineis.append(painel)

        painel = criar_painel("Ruído do canal (AWGN)")
        c1, self.entrada_media = criar_campo("Média:", None, "decimal_sinal", 7)
        c2, self.entrada_desvio = criar_campo("Desvio padrão:", None, "decimal", 7)
        c3, self.entrada_semente = criar_campo("Semente:", None, "inteiro", 9, dica="opcional")
        self.entrada_media.set_text("0")
        self.entrada_desvio.set_text("0")
        painel.append(criar_linha(c1, c2, c3, espaco=22))
        paineis.append(painel)

        rolagem = Gtk.ScrolledWindow()
        rolagem.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        rolagem.set_vexpand(True)
        rolagem.set_child(paineis)

        botao = Gtk.Button(label="Começar Simulação")
        botao.add_css_class("comecar")
        botao.set_halign(Gtk.Align.CENTER)
        botao.set_margin_top(4)
        botao.connect("clicked", self.ao_comecar)

        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        col.set_hexpand(True)
        col.append(rolagem)
        col.append(botao)
        return col

    # ------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------
    def _avisar(self, titulo, detalhe):
        if hasattr(Gtk, "AlertDialog"):
            dialogo = Gtk.AlertDialog()
            dialogo.set_message(titulo)
            dialogo.set_detail(detalhe)
            dialogo.show(self)
        else:
            print(f"{titulo}: {detalhe}")

    def obter_configuracao(self):
        """Lê e valida os parâmetros no formato esperado por simulador.py."""
        edc = selecionado(self.r_edc)
        fisica = selecionado(self.r_fisica)
        quadro, ok1 = ler_numero(self.entrada_quadro, inteiro=True, minimo=0, estrito=True)
        if edc == "checksum":
            edc_tam, ok2 = ler_numero(
                self.entrada_edc, inteiro=True, minimo=0, estrito=True
            )
        else:
            edc_tam, ok2 = None, True
        amplitude, ok3 = ler_numero(self.entrada_voltagem, minimo=0, estrito=True)
        media, ok4 = ler_numero(self.entrada_media)
        desvio, ok5 = ler_numero(self.entrada_desvio, minimo=0)
        semente, ok6 = ler_numero(self.entrada_semente, inteiro=True, minimo=0, obrigatorio=False)
        if edc == "crc":
            edc_tam = 32
        elif edc == "hamming":
            edc_tam = None

        if not all((ok1, ok2, ok3, ok4, ok5, ok6)):
            self._avisar(
                "Verifique os campos destacados",
                "• Quadro: inteiro maior que zero, em bits.\n"
                "• EDC do Checksum: inteiro maior que zero, em bits.\n"
                "• Amplitude: número maior que zero.\n"
                "• Média e desvio padrão: obrigatórios; desvio ≥ 0.\n"
                "• Semente: opcional; inteiro ≥ 0."
            )
            return None

        if edc == "checksum" and (edc_tam is None or edc_tam < 1):
            self.entrada_edc.add_css_class("erro")
            self._avisar("Tamanho de EDC inválido", "Para Checksum, informe o tamanho em bits.")
            return None

        codificacao = fisica if fisica in ("nrz_polar", "bipolar", "manchester") else None
        modulacao = fisica if fisica in ("ASK", "FSK", "8PSK", "32QAM") else None
        return {
            "tamanho_quadro": quadro,
            "tamanho_edc": edc_tam,
            "enquadramento": selecionado(self.r_enquadramento),
            "edc": edc,
            "codificacao": codificacao,
            "modulacao": modulacao,
            "params_fisica": {"V": amplitude},
            "awgn": {"media": media, "desvio_padrao": desvio, "semente": semente},
        }

    def ao_comecar(self, _botao):
        config = self.obter_configuracao()
        if config is None:
            return
        print("Configuração escolhida:", config)

        app = self.get_application()
        try:
            modulo = importlib.import_module(MODULO_CHAT)
            JanelaChat = modulo.JanelaChat
        except (ImportError, AttributeError) as e:
            self._avisar("Tela de chat não encontrada",
                         f"Não consegui importar JanelaChat de '{MODULO_CHAT}.py'.\n{e}")
            return

        if hasattr(modulo, "CSS"):
            app.carregar_css(modulo.CSS)

        a = JanelaChat(app, "Pessoa A")
        b = JanelaChat(app, "Pessoa B")
        a.peer, b.peer = b, a
        a.config = b.config = config  # configuração compartilhada pelas duas pontas
        a.present()
        b.present()
        self.close()


class AppHermes(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.exemplo.Hermes")

    def carregar_css(self, texto):
        css = Gtk.CssProvider()
        if hasattr(css, "load_from_string"):  # GTK >= 4.12
            css.load_from_string(texto)
        else:
            css.load_from_data(texto.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):
        self.carregar_css(CSS)
        JanelaHome(self).present()


if __name__ == "__main__":
    sys.exit(AppHermes().run(sys.argv))