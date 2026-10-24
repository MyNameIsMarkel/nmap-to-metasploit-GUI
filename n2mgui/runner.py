"""runner.py — Ejecuta comandos externos (msfconsole, searchsploit, nmap) en vivo."""

from __future__ import annotations

import re
import shutil

from PyQt5.QtCore import QObject, QProcess, pyqtSignal

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


class CommandRunner(QObject):
    output = pyqtSignal(str)
    started = pyqtSignal(str)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.state() != QProcess.NotRunning

    def run(self, argv: list[str]) -> bool:
        if self.is_running():
            self.error.emit("Ya hay un proceso en ejecución. Deténlo primero.")
            return False
        if not argv:
            return False
        if not have(argv[0]) and not argv[0].startswith("/"):
            self.error.emit(f"No se encuentra '{argv[0]}'. ¿Está instalado?")
            return False
        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.MergedChannels)
        self._proc.readyReadStandardOutput.connect(self._on_read)
        self._proc.finished.connect(self._on_done)
        self._proc.errorOccurred.connect(self._on_err)
        self.started.emit(" ".join(argv))
        self._proc.start(argv[0], argv[1:])
        return True

    def stop(self) -> None:
        if self.is_running() and self._proc is not None:
            self._proc.terminate()
            if not self._proc.waitForFinished(1500):
                self._proc.kill()

    def _on_read(self):
        if self._proc is None:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode("utf-8", "replace")
        self.output.emit(strip_ansi(data))

    def _on_done(self, code, _status):
        self.finished.emit(int(code))
        self._proc = None

    def _on_err(self, err):
        if err == QProcess.FailedToStart:
            self.error.emit("El proceso no pudo arrancar (ruta o permisos).")
