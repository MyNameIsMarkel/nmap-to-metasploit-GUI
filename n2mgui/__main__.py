"""Punto de entrada: python3 -m n2mgui"""

import sys

from PyQt5.QtWidgets import QApplication

from .mainwindow import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("nmap to Metasploit GUI")
    app.setApplicationDisplayName("nmap → Metasploit GUI")
    win = MainWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
