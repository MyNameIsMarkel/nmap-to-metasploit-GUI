"""
matcher.py — Correlaciona servicios detectados con módulos de Metasploit.

Dos vías combinables:
  - Offline: mapa curado (data/modules.json) por servicio/producto/versión y por CVE.
  - En vivo: `msfconsole -q -x "search ..."` para ampliar (opcional, más lento).

Cada coincidencia produce un Match con el módulo, para qué sirve, el rank y los
comandos de msfconsole listos para copiar/ejecutar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .nmapparse import Host, Service

DATA = Path(__file__).resolve().parent / "data" / "modules.json"


@dataclass
class Match:
    host: str
    service_label: str
    port: int
    module: str
    kind: str            # exploit / auxiliary / post ...
    rank: str
    about: str
    source: str          # "offline", "cve:CVE-…", "msf-search"
    options: dict = field(default_factory=dict)

    def commands(self, lhost: str = "TU_IP") -> str:
        """Bloque de comandos msfconsole para este módulo."""
        lines = [f"use {self.module}",
                 f"set RHOSTS {self.host}",
                 f"set RPORT {self.port}"]
        for k, v in self.options.items():
            lines.append(f"set {k} {v}")
        if self.kind == "exploit":
            lines.append(f"set LHOST {lhost}")
            lines.append("show options")
            lines.append("check    # si el módulo lo soporta")
            lines.append("run")
        else:
            lines.append("show options")
            lines.append("run")
        return "\n".join(lines)

    def rc_block(self, lhost: str = "TU_IP") -> str:
        block = self.commands(lhost).splitlines()
        # Quitamos comentarios y 'show options' para el .rc automatizado
        block = [b for b in block if not b.startswith("check") and b != "show options"]
        return "\n".join(block) + "\n"


class Matcher:
    def __init__(self):
        raw = json.loads(DATA.read_text(encoding="utf-8"))
        self._by_service = raw.get("by_service", [])
        self._by_cve = raw.get("by_cve", {})
        self._cve_about = raw.get("cve_about", {})

    # ---------------------------------------------------- offline
    def _svc_matches(self, host: Host, svc: Service) -> list[Match]:
        out: list[Match] = []
        name = (svc.name or "").lower()
        product = (svc.product or "").lower()

        for entry in self._by_service:
            keys = [k.lower() for k in entry.get("match", [])]
            if name and not any(k == name or k in name for k in keys):
                continue
            # Si la entrada exige producto/version, comprobarlo
            want_prod = entry.get("product", "").lower()
            if want_prod and want_prod not in product:
                continue
            want_ver = entry.get("version", "")
            if want_ver and want_ver not in (svc.version or ""):
                continue
            out.append(Match(
                host=host.address, service_label=svc.label, port=svc.port,
                module=entry["module"], kind=entry.get("kind", "auxiliary"),
                rank=entry.get("rank", "normal"), about=entry.get("about", ""),
                source="offline", options=dict(entry.get("set", {})),
            ))

        # Por CVE detectado en NSE/banner
        for cve in svc.cves:
            mod = self._by_cve.get(cve.upper())
            if mod:
                about = self._cve_about.get(cve.upper(), f"Módulo asociado a {cve}.")
                out.append(Match(
                    host=host.address, service_label=svc.label, port=svc.port,
                    module=mod, kind="exploit" if "/exploit/" in f"/{mod}" or mod.startswith("exploit/") else "auxiliary",
                    rank="normal", about=f"[{cve}] {about}", source=f"cve:{cve}",
                ))
        return out

    def match_hosts(self, hosts: list[Host]) -> list[Match]:
        res: list[Match] = []
        seen = set()
        for h in hosts:
            for s in h.services:
                for m in self._svc_matches(h, s):
                    key = (m.host, m.port, m.module)
                    if key not in seen:
                        seen.add(key)
                        res.append(m)
        # Orden: exploits primero, por rank
        rank_order = {"excellent": 0, "great": 1, "good": 2, "normal": 3,
                      "average": 4, "low": 5, "manual": 6}
        res.sort(key=lambda m: (0 if m.kind == "exploit" else 1,
                                rank_order.get(m.rank, 3), m.host, m.port))
        return res

    # ---------------------------------------------------- búsqueda en vivo
    @staticmethod
    def msf_search_command(term: str) -> list[str]:
        """Devuelve el argv para buscar en msfconsole de forma no interactiva."""
        return ["msfconsole", "-q", "-x", f"search {term}; exit"]

    @staticmethod
    def search_terms(hosts: list[Host]) -> list[str]:
        """Términos de búsqueda sugeridos a partir de productos/CVEs vistos."""
        terms: set[str] = set()
        for h in hosts:
            for s in h.services:
                if s.product:
                    terms.add(s.product.split()[0])
                for cve in s.cves:
                    terms.add(cve)
        return sorted(terms)
