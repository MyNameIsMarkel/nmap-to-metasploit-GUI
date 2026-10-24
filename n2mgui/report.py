"""report.py — Exporta los hallazgos a Markdown, CSV o HTML."""

from __future__ import annotations

import csv
import html
import io
from datetime import datetime

from .matcher import Match


def to_markdown(matches: list[Match], lhost: str = "TU_IP") -> str:
    out = ["# Informe nmap → Metasploit",
           f"_Generado: {datetime.now():%Y-%m-%d %H:%M}_", "",
           f"Total de coincidencias: **{len(matches)}**", ""]
    by_host: dict[str, list[Match]] = {}
    for m in matches:
        by_host.setdefault(m.host, []).append(m)
    for host, ms in by_host.items():
        out.append(f"## {host}")
        for m in ms:
            out += [f"### `{m.module}`  ({m.kind}, rank: {m.rank})",
                    f"- **Puerto:** {m.port} — {m.service_label}",
                    f"- **Para qué sirve:** {m.about}",
                    f"- **Origen:** {m.source}",
                    "- **Cómo ejecutarlo:**", "", "```", m.commands(lhost), "```", ""]
    return "\n".join(out)


def to_csv(matches: list[Match]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["host", "puerto", "servicio", "modulo", "tipo", "rank", "origen", "para_que"])
    for m in matches:
        w.writerow([m.host, m.port, m.service_label, m.module, m.kind,
                    m.rank, m.source, m.about])
    return buf.getvalue()


def to_html(matches: list[Match], lhost: str = "TU_IP") -> str:
    e = html.escape
    rows = []
    for m in matches:
        cmds = e(m.commands(lhost))
        rows.append(f"""
        <tr class="{'exploit' if m.kind=='exploit' else 'aux'}">
          <td>{e(m.host)}</td><td>{m.port}</td><td>{e(m.service_label)}</td>
          <td><code>{e(m.module)}</code></td>
          <td>{e(m.kind)}</td><td>{e(m.rank)}</td>
          <td>{e(m.about)}</td>
          <td><pre>{cmds}</pre></td>
        </tr>""")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Informe nmap → Metasploit</title>
<style>
 body{{font-family:system-ui,sans-serif;background:#13100b;color:#f3ede3;margin:24px}}
 h1{{color:#f6873a}} .muted{{color:#b6a992}}
 table{{border-collapse:collapse;width:100%;margin-top:16px;font-size:13px}}
 th,td{{border:1px solid #3a3326;padding:7px 9px;vertical-align:top;text-align:left}}
 th{{background:#231d12;color:#f6873a}}
 tr.exploit td:first-child{{border-left:3px solid #f6873a}}
 code{{color:#ffb673}} pre{{margin:0;white-space:pre-wrap;color:#d7ffd0;font-size:12px}}
</style></head><body>
<h1>Informe nmap → Metasploit</h1>
<p class="muted">Generado: {datetime.now():%Y-%m-%d %H:%M} · {len(matches)} coincidencias ·
Solo para pruebas autorizadas.</p>
<table><thead><tr>
 <th>Host</th><th>Puerto</th><th>Servicio</th><th>Módulo</th><th>Tipo</th>
 <th>Rank</th><th>Para qué sirve</th><th>Cómo ejecutarlo</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table>
</body></html>"""


def to_rc(matches: list[Match], lhost: str = "TU_IP", only_exploits=False) -> str:
    out = [f"# Resource script generado {datetime.now():%Y-%m-%d %H:%M}",
           "# Solo para pruebas autorizadas. Revisa antes de ejecutar.",
           "setg RHOSTS_FILE_NOTE 'revisa cada módulo'", ""]
    for m in matches:
        if only_exploits and m.kind != "exploit":
            continue
        out.append(f"# {m.module} — {m.about}")
        out.append(m.rc_block(lhost))
    return "\n".join(out)
