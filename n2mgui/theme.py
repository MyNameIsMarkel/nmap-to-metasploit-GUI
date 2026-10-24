"""Hoja de estilo (QSS) — base compartida con las demás apps; acento naranja."""

BG = "#0e141d"
PANEL = "#151d2a"
PANEL_2 = "#1c2736"
BORDER = "#2a3850"
TEXT = "#e8eef7"
MUTED = "#8a99b3"
ACCENT = "#f6873a"       # naranja principal
ACCENT_DK = "#db6a1f"
CONSOLE_BG = "#0a0f17"
CONSOLE_TEXT = "#ffd9b8"   # naranja claro para la consola
OK = "#5ac88a"
BAD = "#ef5f5f"
WARN = "#f0c33a"

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
    background: rgba(246,135,58,0.10);
    border: 1px solid rgba(246,135,58,0.45);
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
QPushButton:hover {{ border-color: {ACCENT}; background: #233041; }}
QPushButton:pressed {{ background: #2a3a4d; }}
QPushButton:disabled {{ color: {MUTED}; background: {PANEL}; }}

QPushButton#primary {{
    background: {ACCENT}; color: #1c0f04; font-weight: 700; border: none;
}}
QPushButton#primary:hover {{ background: {ACCENT_DK}; }}
QPushButton#primary:disabled {{ background: #4a3824; color: #ae9177; }}

QPushButton#danger {{
    background: transparent; border: 1px solid {BAD}; color: {BAD};
}}
QPushButton#danger:hover {{ background: rgba(239,95,95,0.12); }}

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
    selection-background-color: rgba(246,135,58,0.22);
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
