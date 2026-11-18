"""Aplicação Hermes: cria as janelas, os menus/atalhos e roda a simulação numa thread."""
import threading
import time
import traceback

from gi.repository import Gio, GLib, Gtk

import simulador as sim
from . import __versao__, estilo
from .janelas import JanelaRX, JanelaTX

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
        estilo.aplicar()
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
