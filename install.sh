#!/usr/bin/env bash
#
# Instalador de nmap → Metasploit GUI.
# - Comprueba python3 + PyQt5.
# - Informa de las herramientas externas útiles (nmap, metasploit, searchsploit).
# - Registra el icono y crea el acceso directo en el menú (KDE) y el Escritorio.
#
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON_SRC="$DIR/n2mgui/resources/icon.png"
RUN="$DIR/run.sh"
APP_ID="nmap-to-metasploit-gui"

ok()   { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; }

command -v python3 >/dev/null 2>&1 || { err "Falta python3 (sudo apt install python3)."; exit 1; }

PYBIN="python3"
if ! "$PYBIN" -c "import PyQt5" >/dev/null 2>&1; then
    warn "Falta PyQt5."
    if command -v apt >/dev/null 2>&1; then
        read -r -p "¿Instalar python3-pyqt5 con apt? [S/n] " a; a=${a:-S}
        [[ "$a" =~ ^[SsYy]$ ]] && sudo apt update && sudo apt install -y python3-pyqt5 || true
    fi
    if ! "$PYBIN" -c "import PyQt5" >/dev/null 2>&1; then
        warn "Creando entorno virtual local (pip)…"
        python3 -m venv "$DIR/.venv"
        "$DIR/.venv/bin/pip" install --upgrade pip >/dev/null
        "$DIR/.venv/bin/pip" install PyQt5
        PYBIN="$DIR/.venv/bin/python"
    fi
fi
ok "Dependencia PyQt5 correcta."

# ---- Herramientas externas (informativo; la correlación offline funciona sin ellas) ----
MISS=()
for t in nmap msfconsole searchsploit; do
    command -v "$t" >/dev/null 2>&1 || MISS+=("$t")
done
if [[ ${#MISS[@]} -gt 0 ]]; then
    warn "No encontradas (opcionales): ${MISS[*]}"
    warn "En Kali:  sudo apt install nmap metasploit-framework exploitdb"
    warn "La app analiza y correlaciona igual (modo offline); estas amplían el flujo en vivo."
else
    ok "nmap, metasploit y searchsploit disponibles."
fi

chmod +x "$RUN"

# ---- Icono ----
for base in "$HOME/.local/share/icons/hicolor/256x256/apps" \
            "$([[ $EUID -eq 0 ]] && echo /usr/share/icons/hicolor/256x256/apps)"; do
    [[ -z "$base" ]] && continue
    mkdir -p "$base" && cp -f "$ICON_SRC" "$base/$APP_ID.png"
done
gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# ---- .desktop (menú) ----
build_desktop() {
    sed -e "s|__EXEC__|$RUN|g" -e "s|__ICON__|$ICON_SRC|g" \
        "$DIR/$APP_ID.desktop.in" > "$1"
    chmod +x "$1"
}

if [[ $EUID -eq 0 && -w /usr/share/applications ]]; then
    MENU_DIR="/usr/share/applications"
else
    MENU_DIR="$HOME/.local/share/applications"
fi
mkdir -p "$MENU_DIR"
build_desktop "$MENU_DIR/$APP_ID.desktop"
update-desktop-database -q "$MENU_DIR" 2>/dev/null || true
ok "Entrada de menú instalada en $MENU_DIR"

# ---- Acceso directo en el Escritorio ----
if [[ -z "${DESKTOP_DIR:-}" ]]; then
    if   [[ -d "$HOME/Escritorio" ]]; then DESKTOP_DIR="$HOME/Escritorio"
    elif [[ -d "$HOME/Desktop" ]];    then DESKTOP_DIR="$HOME/Desktop"
    else DESKTOP_DIR="$HOME/Escritorio"
    fi
fi
mkdir -p "$DESKTOP_DIR"
DESK_FILE="$DESKTOP_DIR/$APP_ID.desktop"
build_desktop "$DESK_FILE"
gio set "$DESK_FILE" metadata::trusted true 2>/dev/null || true
ok "Acceso directo creado en: $DESK_FILE"

kbuildsycoca6 >/dev/null 2>&1 || kbuildsycoca5 >/dev/null 2>&1 || true

echo
ok "Instalación completada."
echo "   Ábrelo desde el menú (busca «nmap» o «Metasploit»), el icono del Escritorio,"
echo "   o ejecutando:  $RUN"
