"""
meme_editor.py — Edição de memes estilo "Pânico na TV" para clips e shorts.

Funcionalidades:
  - "Inchar a cara": Distorção esférica (barrel distortion / lenscorrection) que incha o rosto
    do apresentador/falante no ápice de punchlines, piadas ou reações absurdas.
  - "Punch-in / Zoom cômico": Destaque com aumento de contraste e saturação.
  - Detecção inteligente no transcript: identifica palavras de choque, ironia, gírias e pontuação
    exclamativa dentro da janela do clip.
  - Geração de filtros FFmpeg compatíveis com timeline (enable='between(t,...)') para inclusão
    direta no render sem perda de geração ou re-encoding desnecessário.
"""

from __future__ import annotations

import re
from typing import Any

# Palavras e expressões características de momentos cômicos, surpresa, absurdo e punchlines
COMEDIC_TRIGGER_PATTERNS = [
    re.compile(r'\b(bizarro|bizarra|bizarros|bizarrices)\b', re.IGNORECASE),
    re.compile(r'\b(absurdo|absurda|absurdos|absurdas)\b', re.IGNORECASE),
    re.compile(r'\b(loucura|surreal|inacredit[aá]vel|inacreditavel)\b', re.IGNORECASE),
    re.compile(r'\b(garoteou|garoteada|garoto|garotada)\b', re.IGNORECASE),
    re.compile(r'\b(quebrou|quebrando|falhou|faliu|explodiu)\b', re.IGNORECASE),
    re.compile(r'\b(destruiu|chocou|chocante|mentira|piada)\b', re.IGNORECASE),
    re.compile(r'\b(rid[ií]culo|rid[ií]cula|vergonha|vergonhoso)\b', re.IGNORECASE),
    re.compile(r'\b(bugou|zoado|zoada|gambiarra|gambiarrona)\b', re.IGNORECASE),
    re.compile(r'\b(troll|meme|caraca|caramba|mano|v[eé]i)\b', re.IGNORECASE),
    re.compile(r'\b(meu\s+deus|n[aã]o\s+[eé]\s+poss[ií]vel|olha\s+isso)\b', re.IGNORECASE),
    re.compile(r'\b(ferrou|lascou|lascou-se|deu\s+ruim)\b', re.IGNORECASE),
]


def detect_meme_moments(
    transcript_segments: list[dict[str, Any]] | None,
    clip_start: float,
    clip_end: float,
    max_effects: int = 3,
    min_spacing_seconds: float = 6.0,
    effect_duration: float = 2.0,
) -> list[dict[str, Any]]:
    """Analisa os segmentos da transcrição dentro do clip e identifica momentos para efeito meme.

    Retorna lista de eventos com timestamps relativos ao início do corte (0.0 até clip_duration).
    """
    if not transcript_segments:
        return []

    clip_duration = max(0.0, float(clip_end) - float(clip_start))
    if clip_duration < 3.0:
        return []

    meme_events: list[dict[str, Any]] = []
    last_event_end = -min_spacing_seconds

    for seg in transcript_segments:
        try:
            seg_start = float(seg.get('start', 0))
            seg_end = float(seg.get('end', 0))
            text = str(seg.get('text', ''))
        except (TypeError, ValueError):
            continue

        # Segmento precisa estar dentro ou cruzar o corte
        if seg_end <= clip_start or seg_start >= clip_end:
            continue

        matched_keyword = None
        for pattern in COMEDIC_TRIGGER_PATTERNS:
            match = pattern.search(text)
            if match:
                matched_keyword = match.group(0).lower()
                break

        # Também detecta exclamações fortes com risos
        if not matched_keyword and (
            '!' in text and any(w in text.lower() for w in ('haha', 'kkk', 'rsrs', 'nossa', 'eita'))
        ):
            matched_keyword = 'exclamacao_comica'

        if matched_keyword:
            # Posição relativa ao início do clip
            rel_start = max(0.0, seg_start - clip_start)
            # Evita colocar efeito imediatamente nos primeiros 0.5s ou nos últimos 1.5s
            rel_start = max(0.5, rel_start)
            rel_end = min(clip_duration - 0.5, rel_start + effect_duration)

            if rel_end > rel_start and (rel_start - last_event_end) >= min_spacing_seconds:
                meme_events.append(
                    {
                        'rel_start': round(rel_start, 2),
                        'rel_end': round(rel_end, 2),
                        'keyword': matched_keyword,
                        'type': 'panico_face_bulge',
                    }
                )
                last_event_end = rel_end

            if len(meme_events) >= max_effects:
                break

    return meme_events


def build_panico_face_bulge_filter(
    meme_events: list[dict[str, Any]],
    center_x: float = 0.50,
    center_y: float = 0.38,
    distortion_k1: float = -0.50,
    distortion_k2: float = -0.25,
) -> str:
    """Gera a cláusula de filtro FFmpeg para inchar a cara das pessoas estilo Pânico na TV.

    Usa lenscorrection com distorção esférica (k1 < 0) e saturação/contraste acentuados,
    ativados exclusivamente durante os intervalos definidos pelos eventos.
    """
    if not meme_events:
        return ''

    # Constrói expressão booleana combinando todos os intervalos de meme
    # Exemplo: between(t,1.5,3.5)+between(t,12.0,14.0)
    enable_clauses = [f'between(t,{ev["rel_start"]:.2f},{ev["rel_end"]:.2f})' for ev in meme_events]
    enable_expr = '+'.join(enable_clauses)

    bulge_filter = (
        f'lenscorrection=cx={center_x:.2f}:cy={center_y:.2f}:'
        f'k1={distortion_k1:.2f}:k2={distortion_k2:.2f}:i=bilinear:'
        f"enable='{enable_expr}'"
    )
    pop_filter = f"eq=saturation=1.40:contrast=1.20:enable='{enable_expr}'"

    return f'{bulge_filter},{pop_filter}'
