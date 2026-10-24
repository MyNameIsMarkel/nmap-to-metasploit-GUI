"""Ventana principal de nmap → Metasploit GUI."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import report
from .matcher import Match, Matcher
from .nmapparse import parse
from .runner import CommandRunner, have
from .theme import ACCENT, BAD, MUTED, OK, STYLESHEET, WARN

HERE = Path(__file__).resolve().parent
ICON_PNG = HERE / "resources" / "icon.png"

RANK_COLORS = {
    "excellent": "#5ac88a", "great": "#7fcf6a", "good": "#b6cf5a",
    "normal": "#c7b56a", "average": "#e0a04a", "low": "#d98a52", "manual": "#ef5f5f",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.matcher = Matcher()
        self.runner = CommandRunner(self)
        self.matches: list[Match] = []

        self.setWindowTitle("nmap → Metasploit GUI")
        self.setMinimumSize(1180, 740)
        if ICON_PNG.exists():
            self.setWindowIcon(QIcon(str(ICON_PNG)))
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._wire()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget(objectName="central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._header())
        root.addWidget(self._banner())
        root.addWidget(self._toolbar())

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self._results_panel())
        split.addWidget(self._right_panel())
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(14, 10, 14, 14)
        wl.addWidget(split)
        root.addWidget(wrap, 1)

        self.status = self.statusBar()
        self.status.showMessage("Carga una exportación de nmap (XML) o lanza un escaneo.")

    def _header(self):
        header = QFrame(objectName="header")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 12, 16, 12)
        h.setSpacing(12)
        logo = QLabel()
        if ICON_PNG.exists():
            logo.setPixmap(QPixmap(str(ICON_PNG)).scaled(
                40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        h.addWidget(logo)
        box = QVBoxLayout()
        box.setSpacing(0)
        box.addWidget(QLabel("nmap → Metasploit GUI", objectName="title"))
        box.addWidget(QLabel("Correlaciona servicios de nmap con módulos de Metasploit",
                             objectName="subtitle"))
        h.addLayout(box)
        h.addStretch(1)
        self.count_lbl = QLabel("0 coincidencias")
        self.count_lbl.setStyleSheet(f"color: {MUTED};")
        h.addWidget(self.count_lbl)
        return header

    def _banner(self):
        b = QFrame(objectName="banner")
        bl = QHBoxLayout(b)
        bl.setContentsMargins(14, 8, 14, 8)
        t = QLabel("⚠  Solo para pruebas de penetración autorizadas. Ejecuta módulos "
                   "únicamente contra sistemas de tu propiedad o con permiso explícito "
                   "por escrito. Esta app sugiere y genera comandos; no explota por ti.")
        t.setObjectName("bannerText")
        t.setWordWrap(True)
        bl.addWidget(t)
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(14, 8, 14, 0)
        wl.addWidget(b)
        return wrap

    def _toolbar(self):
        w = QWidget()
        g = QHBoxLayout(w)
        g.setContentsMargins(14, 8, 14, 0)
        g.setSpacing(8)

        self.btn_open = QPushButton("Abrir export nmap…")
        self.btn_open.setObjectName("primary")
        self.btn_open.clicked.connect(self._open_file)
        g.addWidget(self.btn_open)

        self.btn_scan = QPushButton("Escanear ahora…")
        self.btn_scan.setToolTip("Lanza nmap -sV --script vuln y analiza el resultado")
        self.btn_scan.clicked.connect(self._run_nmap)
        g.addWidget(self.btn_scan)

        g.addStretch(1)
        g.addWidget(QLabel("LHOST"))
        self.lhost = QLineEdit()
        self.lhost.setPlaceholderText("tu IP (para exploits)")
        self.lhost.setFixedWidth(150)
        g.addWidget(self.lhost)

        self.btn_export = QPushButton("Exportar informe…")
        self.btn_export.clicked.connect(self._export)
        g.addWidget(self.btn_export)

        self.btn_dbimport = QPushButton("db_import")
        self.btn_dbimport.setToolTip("Comando para importar el XML al workspace de Metasploit")
        self.btn_dbimport.clicked.connect(self._db_import)
        g.addWidget(self.btn_dbimport)

        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.runner.stop)
        g.addWidget(self.btn_stop)
        return w

    def _results_panel(self):
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Host", "Puerto", "Servicio", "Módulo", "Tipo", "Rank"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._on_select)
        return self.table

    def _right_panel(self):
        panel = QWidget()
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)

        self.detail_about = QLabel("Selecciona una coincidencia para ver el detalle.")
        self.detail_about.setObjectName("hint")
        self.detail_about.setWordWrap(True)
        v.addWidget(self.detail_about)

        self.detail_cmds = QPlainTextEdit()
        self.detail_cmds.setReadOnly(True)
        self.detail_cmds.setFont(QFont("DejaVu Sans Mono", 11))
        self.detail_cmds.setPlaceholderText("Aquí aparecerán los comandos de msfconsole.")
        self.detail_cmds.setFixedHeight(190)
        v.addWidget(self.detail_cmds)

        row = QHBoxLayout()
        b_copy = QPushButton("Copiar comandos")
        b_copy.clicked.connect(self._copy_cmds)
        row.addWidget(b_copy)
        b_msf = QPushButton("Buscar en msfconsole")
        b_msf.setToolTip("Búsqueda en vivo del módulo/producto en Metasploit")
        b_msf.clicked.connect(self._msf_search)
        row.addWidget(b_msf)
        b_ss = QPushButton("searchsploit")
        b_ss.setToolTip("Busca en ExploitDB el producto/servicio seleccionado")
        b_ss.clicked.connect(self._searchsploit)
        row.addWidget(b_ss)
        v.addLayout(row)

        v.addWidget(QLabel("Consola", objectName="hint"))
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("DejaVu Sans Mono", 10))
        self.console.setPlaceholderText(
            "Salida de nmap / msfconsole / searchsploit en vivo.")
        v.addWidget(self.console, 1)

        util = QHBoxLayout()
        clr = QPushButton("Limpiar consola"); clr.setFixedWidth(130)
        clr.clicked.connect(self.console.clear)
        util.addWidget(clr)
        util.addStretch(1)
        ab = QPushButton("Acerca de"); ab.setFixedWidth(100)
        ab.clicked.connect(self._about)
        util.addWidget(ab)
        v.addLayout(util)
        return panel

    # -------------------------------------------------------------- lógica
    def _wire(self):
        self.runner.output.connect(lambda t: self.console.insertPlainText(t))
        self.runner.started.connect(self._on_started)
        self.runner.finished.connect(self._on_finished)
        self.runner.error.connect(lambda m: self.console.appendPlainText(f"\n[!] {m}\n"))

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir exportación de nmap", "",
            "nmap (*.xml *.nmap *.gnmap);;Todos (*)")
        if path:
            self._load(path)

    def _load(self, path: str):
        try:
            hosts = parse(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error al parsear",
                                 f"No se pudo leer el archivo:\n{exc}")
            return
        self.matches = self.matcher.match_hosts(hosts)
        self._fill_table()
        nh = len(hosts)
        self.status.showMessage(f"{nh} host(s) · {len(self.matches)} coincidencias "
                                f"desde {os.path.basename(path)}")
        if not self.matches:
            self.console.appendPlainText(
                "\n[i] No hubo coincidencias en el mapa offline. Prueba «Buscar en "
                "msfconsole» con un producto, o revisa que el XML tenga -sV.\n")

    def _fill_table(self):
        self.table.setRowCount(0)
        for m in self.matches:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [m.host, str(m.port), m.service_label, m.module, m.kind, m.rank]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if c == 5:
                    it.setForeground(QColor(RANK_COLORS.get(m.rank, "#c7b56a")))
                if c == 4 and m.kind == "exploit":
                    it.setForeground(QColor(ACCENT))
                self.table.setItem(r, c, it)
        self.count_lbl.setText(f"{len(self.matches)} coincidencias")

    def _current(self) -> Match | None:
        row = self.table.currentRow()
        if 0 <= row < len(self.matches):
            return self.matches[row]
        return None

    def _on_select(self):
        m = self._current()
        if not m:
            return
        self.detail_about.setText(
            f"<b>{m.module}</b> &nbsp;<span style='color:{MUTED}'>"
            f"({m.kind}, rank {m.rank}, origen {m.source})</span><br>{m.about}")
        self.detail_cmds.setPlainText(m.commands(self.lhost.text().strip() or "TU_IP"))

    def _copy_cmds(self):
        from PyQt5.QtWidgets import QApplication
        if self.detail_cmds.toPlainText():
            QApplication.clipboard().setText(self.detail_cmds.toPlainText())
            self.status.showMessage("Comandos copiados al portapapeles.")

    # ----- acciones externas
    def _run_nmap(self):
        if not have("nmap"):
            QMessageBox.warning(self, "nmap", "nmap no está instalado.")
            return
        target, ok = QInputDialog.getText(
            self, "Escanear con nmap",
            "Objetivo (IP, rango o host) — solo con autorización:")
        if not ok or not target.strip():
            return
        self._nmap_xml = os.path.join(tempfile.gettempdir(),
                                      "n2m_scan.xml")
        argv = ["nmap", "-sV", "--script", "vuln", "-oX", self._nmap_xml,
                target.strip()]
        self.console.appendPlainText(f"\n$ {' '.join(argv)}\n")
        self._pending_parse = self._nmap_xml
        self.runner.run(argv)

    def _msf_search(self):
        m = self._current()
        term = m.module.split("/")[-1] if m else ""
        term, ok = QInputDialog.getText(
            self, "Buscar en msfconsole", "Término de búsqueda:", text=term)
        if not ok or not term.strip():
            return
        self.console.appendPlainText(f"\n$ msfconsole -q -x 'search {term.strip()}'\n")
        self.runner.run(self.matcher.msf_search_command(term.strip()))

    def _searchsploit(self):
        m = self._current()
        default = ""
        if m:
            # usa el producto del label si lo hay
            default = m.service_label.split(" ", 2)[-1][:40]
        term, ok = QInputDialog.getText(
            self, "searchsploit", "Buscar en ExploitDB:", text=default)
        if not ok or not term.strip():
            return
        self.console.appendPlainText(f"\n$ searchsploit {term.strip()}\n")
        self.runner.run(["searchsploit"] + term.strip().split())

    def _db_import(self):
        if not getattr(self, "_nmap_xml", None) and not hasattr(self, "_last_xml"):
            QMessageBox.information(
                self, "db_import",
                "Abre o genera primero un XML de nmap. Luego este botón te da el "
                "comando para importarlo a Metasploit.")
            return
        xml = getattr(self, "_nmap_xml", getattr(self, "_last_xml", "salida.xml"))
        cmd = (f"msfconsole -q -x \"workspace -a auditoria; db_import {xml}; "
               f"hosts; services; exit\"")
        self.console.appendPlainText(
            "\n[db_import] Ejecuta esto para cargar el escaneo en Metasploit:\n"
            f"{cmd}\n")
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(cmd)
        self.status.showMessage("Comando db_import copiado al portapapeles.")

    def _export(self):
        if not self.matches:
            QMessageBox.information(self, "Exportar", "No hay coincidencias que exportar.")
            return
        path, filt = QFileDialog.getSaveFileName(
            self, "Exportar informe", "informe-nmap-metasploit",
            "HTML (*.html);;Markdown (*.md);;CSV (*.csv);;Resource script (*.rc)")
        if not path:
            return
        lh = self.lhost.text().strip() or "TU_IP"
        if path.endswith(".md") or "Markdown" in filt:
            data = report.to_markdown(self.matches, lh)
        elif path.endswith(".csv") or "CSV" in filt:
            data = report.to_csv(self.matches)
        elif path.endswith(".rc") or "Resource" in filt:
            data = report.to_rc(self.matches, lh)
        else:
            data = report.to_html(self.matches, lh)
            if not path.endswith(".html"):
                path += ".html"
        Path(path).write_text(data, encoding="utf-8")
        self.status.showMessage(f"Informe guardado en {path}")

    # ----- runner callbacks
    def _on_started(self, cmd):
        self.btn_stop.setEnabled(True)
        self.status.showMessage(f"Ejecutando: {cmd[:80]}…")

    def _on_finished(self, code):
        self.btn_stop.setEnabled(False)
        self.console.appendPlainText(f"\n[fin · código {code}]\n")
        pend = getattr(self, "_pending_parse", None)
        if pend and os.path.exists(pend):
            self._pending_parse = None
            self._last_xml = pend
            self.console.appendPlainText("[i] Analizando el XML del escaneo…\n")
            self._load(pend)

    def _about(self):
        QMessageBox.information(
            self, "Acerca de",
            "<b>nmap → Metasploit GUI</b><br>"
            "Correlaciona servicios detectados por nmap con módulos de Metasploit, "
            "explica para qué sirven y genera los comandos.<br><br>"
            "Mapa offline + búsqueda en vivo (msfconsole) + searchsploit.<br>"
            "No explota por ti: genera comandos para pruebas autorizadas.")

    def closeEvent(self, event):
        self.runner.stop()
        super().closeEvent(event)
