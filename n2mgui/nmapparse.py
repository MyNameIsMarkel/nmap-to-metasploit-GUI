"""
nmapparse.py — Parsea una exportación de nmap.

Soporta:
  - XML de nmap (`nmap -oX salida.xml`)  → formato recomendado y completo.
  - Salida normal (`.nmap`) como respaldo → extracción básica por regex.

Devuelve una lista de Host, cada uno con sus Service (puertos abiertos),
incluyendo producto/versión, salida de scripts NSE y CVEs detectados.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


@dataclass
class Service:
    port: int
    proto: str = "tcp"
    state: str = "open"
    name: str = ""          # servicio (http, ssh, microsoft-ds…)
    product: str = ""       # p. ej. "Apache httpd"
    version: str = ""       # p. ej. "2.4.49"
    extrainfo: str = ""
    cpe: list[str] = field(default_factory=list)
    scripts: dict[str, str] = field(default_factory=dict)  # id NSE -> salida
    cves: list[str] = field(default_factory=list)

    @property
    def banner(self) -> str:
        bits = [self.product, self.version, self.extrainfo]
        return " ".join(b for b in bits if b).strip()

    @property
    def label(self) -> str:
        return f"{self.port}/{self.proto} {self.name} {self.banner}".strip()


@dataclass
class Host:
    address: str
    hostname: str = ""
    state: str = "up"
    services: list[Service] = field(default_factory=list)

    @property
    def display(self) -> str:
        return f"{self.address}" + (f" ({self.hostname})" if self.hostname else "")


def _collect_cves(text: str) -> list[str]:
    return sorted({m.upper() for m in CVE_RE.findall(text or "")})


def parse_xml(path: str) -> list[Host]:
    tree = ET.parse(path)
    root = tree.getroot()
    hosts: list[Host] = []

    for h in root.findall("host"):
        st = h.find("status")
        if st is not None and st.get("state") == "down":
            continue
        addr = ""
        for a in h.findall("address"):
            if a.get("addrtype") in ("ipv4", "ipv6"):
                addr = a.get("addr", "")
                break
        if not addr:
            # a veces solo hay MAC
            a = h.find("address")
            addr = a.get("addr", "") if a is not None else "?"

        hostname = ""
        hn = h.find("hostnames/hostname")
        if hn is not None:
            hostname = hn.get("name", "")

        host = Host(address=addr, hostname=hostname)

        for p in h.findall("ports/port"):
            state_el = p.find("state")
            state = state_el.get("state") if state_el is not None else "unknown"
            if state != "open":
                continue
            svc = Service(
                port=int(p.get("portid", "0")),
                proto=p.get("protocol", "tcp"),
                state=state,
            )
            s = p.find("service")
            if s is not None:
                svc.name = s.get("name", "") or ""
                svc.product = s.get("product", "") or ""
                svc.version = s.get("version", "") or ""
                svc.extrainfo = s.get("extrainfo", "") or ""
                svc.cpe = [c.text for c in s.findall("cpe") if c.text]
            for sc in p.findall("script"):
                sid = sc.get("id", "")
                out = sc.get("output", "") or ""
                svc.scripts[sid] = out
                svc.cves += _collect_cves(out)
            # CVEs también en el banner/cpe
            svc.cves += _collect_cves(svc.banner)
            svc.cves = sorted(set(svc.cves))
            host.services.append(svc)

        # Scripts a nivel de host (hostscript)
        for sc in h.findall("hostscript/script"):
            out = sc.get("output", "") or ""
            if host.services:
                host.services[0].scripts.setdefault("host:" + sc.get("id", ""), out)

        hosts.append(host)

    return hosts


def parse_nmap_text(path: str) -> list[Host]:
    """Respaldo para salida normal de nmap (.nmap). Extracción básica."""
    hosts: list[Host] = []
    current: Host | None = None
    port_re = re.compile(r"^(\d+)/(tcp|udp)\s+open\s+(\S+)\s*(.*)$")
    host_re = re.compile(r"Nmap scan report for (\S+)(?:\s+\(([\d.]+)\))?")

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            m = host_re.search(line)
            if m:
                if current:
                    hosts.append(current)
                name, ip = m.group(1), m.group(2)
                if ip:
                    current = Host(address=ip, hostname=name)
                else:
                    current = Host(address=name)
                continue
            if current:
                pm = port_re.match(line.strip())
                if pm:
                    port, proto, name, rest = pm.groups()
                    svc = Service(port=int(port), proto=proto, name=name)
                    # rest ~ "Apache httpd 2.4.49 ((Unix))"
                    svc.product = rest.strip()
                    svc.cves = _collect_cves(rest)
                    current.services.append(svc)
    if current:
        hosts.append(current)
    return hosts


def parse(path: str) -> list[Host]:
    """Detecta el formato por contenido y delega."""
    with open(path, "rb") as fh:
        head = fh.read(256)
    if b"<?xml" in head or b"<nmaprun" in head:
        return parse_xml(path)
    return parse_nmap_text(path)
