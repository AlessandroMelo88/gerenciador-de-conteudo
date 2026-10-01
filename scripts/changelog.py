#!/usr/bin/env python3
"""changelog.py — monta o CHANGELOG.md (formato Release Notes) a partir de CHANGELOG.d/.

Fragmentos: CHANGELOG.d/<slug>.<tipo>.md, com tipo em {novidade, melhoria, correcao, tecnico}.
Cada linha não vazia do fragmento vira um item; linhas que já começam com "- [" são mantidas,
linhas iniciadas por espaço são tratadas como continuação do item anterior.

Uso:
  scripts/changelog.py preview                       # imprime a seção [Unreleased] montada
  scripts/changelog.py release vX.Y.Z [--date D] [--keep] [--dry-run]
      move os fragmentos para uma seção "## [vX.Y.Z (D)](<compare>)" no CHANGELOG.md e os apaga
      (--keep mantém; --dry-run só imprime o resultado)

Só stdlib. Não faz bump de versão nem tag — ver Docs/operacao/DESENVOLVIMENTO.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FRAG_DIR = ROOT / 'CHANGELOG.d'
CHANGELOG = ROOT / 'CHANGELOG.md'
REPO_URL = 'https://github.com/AlessandroMelo88/gerenciador-de-conteudo'
SECTIONS = (
    ('novidade', '### ✨ Novidades'),
    ('melhoria', '### 🎨 Melhorias'),
    ('correcao', '### 🐛 Correções'),
    ('tecnico', '### 🔧 Técnico'),
)
TYPES = {k for k, _ in SECTIONS}
UNRELEASED_NOTE = (
    '_Itens pendentes vivem em `CHANGELOG.d/` — `make changelog-preview` monta esta seção; '
    '`make changelog-release VERSION=vX.Y.Z` fecha a versão._'
)
VERSION_RE = re.compile(r'^## \[(v\d+\.\d+\.\d+) \((\d{4}-\d{2}-\d{2})\)\]', re.M)
UNRELEASED_RE = re.compile(r'^## \[Unreleased\][^\n]*$', re.M)
HEADING_RE = re.compile(r'^## \[', re.M)


def load_fragments() -> dict[str, list[str]]:
    items: dict[str, list[str]] = {k: [] for k in TYPES}
    for path in sorted(FRAG_DIR.glob('*.md')):
        if path.name.lower() == 'readme.md' or path.name.startswith('_'):
            continue
        stem, _, kind = path.name[:-3].rpartition('.')
        if not stem or kind not in TYPES:
            sys.exit(f'fragmento inválido: {path.name} — esperado <slug>.<{"|".join(sorted(TYPES))}>.md')
        for raw in path.read_text(encoding='utf-8').splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            if line.startswith((' ', '\t')):
                items[kind].append(line)
            elif line.lstrip().startswith('- ['):
                items[kind].append(line)
            elif line.lstrip().startswith('- '):
                items[kind].append(line.replace('- ', '- [x] ', 1))
            else:
                items[kind].append(f'- [x] {line}')
    return items


def render(items: dict[str, list[str]]) -> str:
    out: list[str] = []
    for key, title in SECTIONS:
        if items[key]:
            out.append(title)
            out.extend(items[key])
            out.append('')
    return '\n'.join(out).rstrip('\n') + '\n' if out else ''


def cmd_preview() -> int:
    body = render(load_fragments())
    print('## [Unreleased]\n')
    print(body if body else '(nenhum fragmento em CHANGELOG.d/)')
    return 0


def cmd_release(version: str, date: str, keep: bool, dry_run: bool) -> int:
    if not re.fullmatch(r'v\d+\.\d+\.\d+', version):
        sys.exit('versão deve ter o formato vX.Y.Z (com o prefixo v)')
    body = render(load_fragments())
    if not body:
        sys.exit('nenhum fragmento em CHANGELOG.d/ — nada para lançar')
    text = CHANGELOG.read_text(encoding='utf-8')
    if version in {m.group(1) for m in VERSION_RE.finditer(text)}:
        sys.exit(f'{version} já existe no CHANGELOG.md')
    marker = UNRELEASED_RE.search(text)
    if not marker:
        sys.exit('CHANGELOG.md sem seção "## [Unreleased]"')
    prev = VERSION_RE.search(text)
    link = f'{REPO_URL}/compare/{prev.group(1)}...{version}' if prev else f'{REPO_URL}/releases/tag/{version}'
    after = text[marker.end():]
    nxt = HEADING_RE.search(after)
    end_unreleased = marker.end() + (nxt.start() if nxt else len(after))
    block = f'## [{version} ({date})]({link})\n\n{body}\n'
    new_text = text[: marker.end()] + '\n\n' + UNRELEASED_NOTE + '\n\n' + block + text[end_unreleased:]
    new_text = new_text.rstrip('\n') + '\n'
    if dry_run:
        print(new_text)
        return 0
    CHANGELOG.write_text(new_text, encoding='utf-8')
    if not keep:
        for path in FRAG_DIR.glob('*.md'):
            if path.name.lower() != 'readme.md' and not path.name.startswith('_'):
                path.unlink()
    print(f'CHANGELOG.md: seção {version} ({date}) criada — link {link}')
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('preview')
    rel = sub.add_parser('release')
    rel.add_argument('version')
    rel.add_argument('--date', default=dt.date.today().isoformat())
    rel.add_argument('--keep', action='store_true', help='não apaga os fragmentos')
    rel.add_argument('--dry-run', action='store_true', help='imprime o CHANGELOG resultante sem gravar')
    args = parser.parse_args(argv)
    if args.cmd == 'preview':
        return cmd_preview()
    return cmd_release(args.version, args.date, args.keep, args.dry_run)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
