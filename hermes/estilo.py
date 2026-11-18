"""Tema visual "Windows 95 / software de rede dos anos 90" em CSS do GTK 4."""
from gi.repository import Gdk, Gtk

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
