"""Ponto de entrada:  python -m hermes   (a partir da raiz do repositório)."""
import sys

import gi
gi.require_version("Gtk", "4.0")

from hermes.app import AppHermes


def main():
    return AppHermes().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
