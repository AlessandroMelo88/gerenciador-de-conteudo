#!/usr/bin/env python3
"""Compila as camadas YAML de prompts (geral + canal + alvo) em perfis JSON.

Porte em Python de scripts/compile_prompt_profiles.rb do release/rico: o
projeto não tem Ruby como dependência. Precisa de PyYAML (``pip install pyyaml``).

Entrada  : prompts/layers/general.yaml, prompts/targets/*.yaml, prompts/channels/*.yaml
Saída    : prompts/compiled/<slug>.json (um por canal) com as colunas de ``prompt_profiles``
Opcional : ``--apply`` faz upsert dessas linhas no banco (usa as variáveis de ambiente
           do clip-processor, ver src/db.py).

Uso:
    python3 scripts/compile_prompt_profiles.py [--channel ID] [--output-dir DIR] [--apply]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / 'prompts'

FIELD_MAP = {
    'youtube-shorts': {'format': 'curto', 'selection': 'selection_short_prompt', 'metadata': 'metadata_short_prompt'},
    'youtube-long': {'format': 'longo', 'selection': 'selection_long_prompt', 'metadata': 'metadata_long_prompt'},
}

REQUIRED_FIELDS = (
    'slug', 'name', 'niche', 'niche_aliases', 'active', 'selection_short_prompt',
    'selection_long_prompt', 'metadata_short_prompt', 'metadata_long_prompt', 'thumbnail_prompt',
)


class ProfileError(Exception):
    """YAML inválido ou incompleto; a mensagem diz qual arquivo/campo."""


def load_yaml(path: Path) -> dict:
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        raise ProfileError(f'YAML inválido em {path}: {exc}') from exc
    except OSError as exc:
        raise ProfileError(f'Não foi possível ler {path}: {exc}') from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProfileError(f'YAML de {path} deve ser um mapa')
    return data


def require_text(value, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f'Campo de texto ausente ou vazio: {context}')
    return value.strip()


def stage_text(config: dict, stage: str, context: str) -> str:
    stage_config = (config.get('stages') or {}).get(stage)
    if not isinstance(stage_config, dict):
        raise ProfileError(f'Etapa {stage} ausente em {context}')
    return require_text(stage_config.get('instructions'), f'{context}.stages.{stage}.instructions')


def prompt_block(title: str, *instructions: str) -> str:
    return '\n\n'.join([title, *[i.strip() for i in instructions]])


def compile_channel(general: dict, channel: dict, targets: dict[str, dict], origin: str = 'canal') -> dict:
    """Devolve o dict com as colunas de ``prompt_profiles`` para um canal."""
    profile = channel.get('profile') or {}
    target_ids = channel.get('targets')
    if not isinstance(target_ids, list) or not target_ids:
        raise ProfileError(f'targets deve ser uma lista não vazia em {origin}')

    payload = {
        'slug': require_text(profile.get('slug'), f'{origin}.profile.slug'),
        'name': require_text(profile.get('name'), f'{origin}.profile.name'),
        'niche': require_text(profile.get('niche'), f'{origin}.profile.niche'),
        'niche_aliases': [
            require_text(v, f'{origin}.profile.niche_aliases[]') for v in (profile.get('niche_aliases') or [])
        ],
        'active': bool(profile.get('active', True)),
    }

    g = {s: stage_text(general, s, 'general') for s in ('selection', 'metadata', 'thumbnail')}
    c = {s: stage_text(channel, s, origin) for s in ('selection', 'metadata', 'thumbnail')}

    thumbnail_rules = []
    for target_id in target_ids:
        mapping = FIELD_MAP.get(target_id)
        if not mapping:
            raise ProfileError(f'Alvo não mapeado para as colunas de prompt_profiles: {target_id}')
        target_file = targets.get(target_id)
        if not target_file:
            raise ProfileError(f'Arquivo YAML ausente para alvo: {target_id}')
        target = target_file.get('target') or {}
        fmt = require_text(target.get('format'), f'{target_id}.target.format')
        if fmt != mapping['format']:
            raise ProfileError(f'Formato inesperado para {target_id}: {fmt}')
        label = require_text(target.get('label'), f'{target_id}.target.label')
        for stage in ('selection', 'metadata'):
            payload[mapping[stage]] = prompt_block(
                'Camada geral', g[stage],
                'Camada do canal de destino', c[stage],
                f'Camada do alvo {label}', stage_text(target_file, stage, target_id),
            )
        thumbnail_rules.append(f'Alvo: {label}\n{stage_text(target_file, "thumbnail", target_id)}')

    payload['thumbnail_prompt'] = prompt_block(
        'Camada geral', g['thumbnail'],
        'Camada do canal de destino', c['thumbnail'],
        'Use somente a regra correspondente ao formato informado pelo pipeline.',
        '\n\n'.join(thumbnail_rules),
    )
    for field in REQUIRED_FIELDS:
        if payload.get(field) is None:
            raise ProfileError(
                f'Campo ausente em {origin}: {field} (o canal precisa dos alvos curto e longo)')
    return payload


def load_targets(targets_dir: Path) -> dict[str, dict]:
    targets = {}
    for path in sorted(targets_dir.glob('*.yaml')):
        data = load_yaml(path)
        targets[require_text((data.get('target') or {}).get('id'), f'{path}.target.id')] = data
    return targets


def compile_all(prompts_dir: Path, channel_filter: str | None = None) -> list[dict]:
    general = load_yaml(prompts_dir / 'layers' / 'general.yaml')
    paths = sorted((prompts_dir / 'channels').glob('*.yaml'))
    if channel_filter:
        paths = [p for p in paths if p.stem == channel_filter]
    if not paths:
        raise ProfileError('Nenhum arquivo de canal (prompts/channels/*.yaml) corresponde ao pedido.')
    targets = load_targets(prompts_dir / 'targets')
    payloads, seen = [], set()
    for path in paths:
        channel = load_yaml(path)
        require_text(channel.get('channel_id'), f'{path}.channel_id')
        payload = compile_channel(general, channel, targets, origin=str(path))
        if payload['slug'] in seen:
            raise ProfileError(f'Slug de perfil duplicado: {payload["slug"]}')
        seen.add(payload['slug'])
        payloads.append(payload)
    return payloads


def apply_to_db(payloads: list[dict]) -> None:
    sys.path.insert(0, str(ROOT / 'clip-processor'))
    from src.db import get_db_connection

    conn = get_db_connection()
    cols = [
        'slug', 'name', 'niche', 'niche_aliases', 'selection_short_prompt', 'selection_long_prompt',
        'metadata_short_prompt', 'metadata_long_prompt', 'thumbnail_prompt', 'active',
    ]
    sql = (
        f'INSERT INTO prompt_profiles ({", ".join(cols)}, created_at, updated_at) '
        f'VALUES ({", ".join(["%s"] * len(cols))}, NOW(), NOW()) '
        'ON CONFLICT (slug) DO UPDATE SET '
        + ', '.join(f'{c} = EXCLUDED.{c}' for c in cols if c != 'slug')
        + ', updated_at = NOW()'
    )
    with conn.cursor() as cur:
        for p in payloads:
            row = [json.dumps(p[c], ensure_ascii=False) if c == 'niche_aliases' else p[c] for c in cols]
            cur.execute(sql, row)
    conn.commit()
    print(f'{len(payloads)} perfil(is) gravado(s) em prompt_profiles')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--channel', help='compila apenas prompts/channels/<ID>.yaml')
    parser.add_argument('--output-dir', default=str(PROMPTS_DIR / 'compiled'))
    parser.add_argument('--apply', action='store_true', help='upsert em prompt_profiles (PostgreSQL)')
    args = parser.parse_args(argv)
    try:
        payloads = compile_all(PROMPTS_DIR, args.channel)
    except ProfileError as exc:
        print(f'ERRO: {exc}', file=sys.stderr)
        return 1
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for payload in payloads:
        path = out / f'{payload["slug"]}.json'
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Gerado {path}')
    if args.apply:
        apply_to_db(payloads)
    return 0


if __name__ == '__main__':
    sys.exit(main())
