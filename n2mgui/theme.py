"""Hoja de estilo (QSS) — base compartida con las demás apps; acento naranja."""

BG = "#000000"
PANEL = "#0c0c0c"
PANEL_2 = "#161616"
BORDER = "#2b2b2b"
TEXT = "#f4f4f4"
MUTED = "#8c8c8c"
ACCENT = "#ffffff"       # naranja principal
ACCENT_DK = "#cccccc"
CONSOLE_BG = "#000000"
CONSOLE_TEXT = "#e8e8e8"   # naranja claro para la consola
OK = "#ffffff"
BAD = "#d7d7d7"
WARN = "#a8a8a8"

STYLESHEET = f"""
* {{
    font-family: "Inter", "Segoe UI", "Cantarell", sans-serif;
    font-size: 13px;
    color: {TEXT};
}}
QMainWindow, QWidget#central {{ background: {BG}; }}

QFrame#header {{ background: {PANEL}; border-bottom: 1px solid {BORDER}; }}
QLabel#title {{ font-size: 17px; font-weight: 700; color: {TEXT}; }}
QLabel#subtitle {{ color: {MUTED}; font-size: 12px; }}

QFrame#banner {{
    background: rgba(159, 159, 159,0.10);
    border: 1px solid rgba(159, 159, 159,0.45);
    border-radius: 8px;
}}
QLabel#bannerText {{ color: {ACCENT}; font-size: 12px; }}

QPushButton {{
    background: {PANEL_2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT};
}}
QPushButton:hover {{ border-color: {ACCENT}; background: #2e2e2e; }}
QPushButton:pressed {{ background: #373737; }}
QPushButton:disabled {{ color: {MUTED}; background: {PANEL}; }}

QPushButton#primary {{
    background: {ACCENT}; color: #121212; font-weight: 700; border: none;
}}
QPushButton#primary:hover {{ background: {ACCENT_DK}; }}
QPushButton#primary:disabled {{ background: #3b3b3b; color: #979797; }}

QPushButton#danger {{
    background: transparent; border: 1px solid {BAD}; color: {BAD};
}}
QPushButton#danger:hover {{ background: rgba(138, 138, 138,0.12); }}

QPlainTextEdit, QTextEdit {{
    background: {CONSOLE_BG};
    color: {CONSOLE_TEXT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    font-family: "JetBrains Mono", "DejaVu Sans Mono", "Consolas", monospace;
    font-size: 12.5px;
    padding: 10px;
    selection-background-color: {ACCENT_DK};
}}

QLineEdit, QComboBox {{
    background: {CONSOLE_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 10px;
    color: {TEXT};
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}

QTableWidget {{
    background: {CONSOLE_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    gridline-color: {BORDER};
    selection-background-color: rgba(159, 159, 159,0.22);
    selection-color: {TEXT};
}}
QTableWidget::item {{ padding: 4px 6px; }}
QHeaderView::section {{
    background: {PANEL_2}; color: {ACCENT}; border: none;
    border-bottom: 1px solid {BORDER}; padding: 7px; font-weight: 600;
}}

QSplitter::handle {{ background: {BORDER}; width: 2px; }}

QStatusBar {{ background: {PANEL}; color: {MUTED}; border-top: 1px solid {BORDER}; }}
QStatusBar::item {{ border: none; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {MUTED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

QLabel#hint {{ color: {MUTED}; font-size: 12px; }}
"""
