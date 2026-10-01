#!/usr/bin/env python3
"""Verifica links relativos dos .md do repositório e caminhos `Docs/...` citados em texto.

Uso: python3 scripts/check-doc-links.py        (sai com 1 se houver link quebrado)

Só stdlib. Ignora graphify-out/, node_modules/, vendor/ e links externos (http, mailto, file).
Âncoras (#...) só são conferidas para arquivos .md. Roda a partir de qualquer pasta do repo.
"""
import os
import re
import subprocess
import sys

ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
os.chdir(ROOT)

LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|!\[[^\]]*\]\(([^)\s]+)\)")
CRASES = re.compile(r"`((?:Docs|\.claude|scripts)/[A-Za-z0-9_./-]+\.(?:md|sh|py))`")
HEAD = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")


def slug(t: str) -> str:
    t = re.sub(r"[`*\[\]()]", "", t.strip().lower())
    t = re.sub(r"[^\w\s-]", "", t, flags=re.UNICODE)
    return re.sub(r"\s", "-", t)


def anchors(path: str) -> set:
    out, fence = set(), False
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("```"):
            fence = not fence
        if fence:
            continue
        m = HEAD.match(ln)
        if m:
            out.add(slug(m.group(1)))
    return out


files = subprocess.check_output(
    ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], text=True
).split("\0")
mds = [
    f for f in files
    if f.endswith(".md") and os.path.isfile(f)
    and not f.startswith(("graphify-out/", "Claude outputs/", ".planning/"))
    and "node_modules/" not in f and "/vendor/" not in f
]

broken, soft, total = [], [], 0
cache = {}
for f in mds:
    text = open(f, encoding="utf-8").read()
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    for m in LINK.finditer(body):
        tgt = m.group(1) or m.group(2)
        if re.match(r"^(https?:|mailto:|file:|data:|tel:)", tgt):
            continue
        total += 1
        path, _, anchor = tgt.partition("#")
        dest = f if not path else os.path.normpath(os.path.join(os.path.dirname(f), path))
        if not os.path.exists(dest):
            broken.append((f, tgt, "arquivo não existe"))
            continue
        if anchor and dest.endswith(".md") and not re.match(r"^L\d+", anchor):
            cache.setdefault(dest, anchors(dest))
            if anchor.lower() not in cache[dest]:
                soft.append((f, tgt, "âncora não encontrada"))
    for m in CRASES.finditer(body):
        total += 1
        if not os.path.exists(m.group(1)):
            broken.append((f, m.group(1), "caminho citado em crases não existe"))

print(f"{len(mds)} arquivos .md, {total} referências conferidas")
for f, t, why in broken:
    print(f"QUEBRADO  {f}: {t}  ({why})")
for f, t, why in soft:
    print(f"AVISO     {f}: {t}  ({why})")
print(f"quebrados: {len(broken)} | avisos de âncora: {len(soft)}")
sys.exit(1 if broken else 0)
