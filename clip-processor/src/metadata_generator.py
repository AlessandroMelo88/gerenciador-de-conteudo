"""
metadata_generator.py — Geração de título, descrição e tags para YouTube.

Exporta:
  - generate_metadata(clip_context, anthropic_client=None) -> dict
  - update_clip_metadata(conn, clip_id, metadata) -> None
  - append_credits(description, credit_template, channel_handle) -> str

Convenções:
  - anthropic_client=None cria cliente de produção; injetado em testes
  - title deve respeitar o limite de 100 caracteres do YouTube
  - tags são persistidas em generated_clips.tags como texto
"""
import json
from datetime import datetime


SYSTEM_PROMPT = (
    "Você é especialista em SEO para YouTube Shorts no nicho de futebol brasileiro. "
    "Gere metadados chamativos, claros e honestos para um corte curto. "
    "O título deve ter no máximo 100 caracteres. "
    "A descrição deve resumir o momento e incluir contexto para retenção. "
    "As tags devem ser termos curtos em PT-BR, sem hashtag, focados em futebol, cortes e tema do vídeo."
)

METADATA_OUTPUT_SCHEMA = {
    'format': {
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'tags': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
            },
            'required': ['title', 'description', 'tags'],
            'additionalProperties': False,
        },
    }
}


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def _normalize_metadata(metadata: dict, clip_context: dict | None = None) -> dict:
    """Normaliza metadata retornada pela IA ou fallback."""
    title = str(metadata.get('title') or '').strip()
    description = str(metadata.get('description') or '').strip()
    tags = metadata.get('tags') or []

    if not title:
        source_title = (clip_context or {}).get('source_title') or 'Corte de futebol'
        title = str(source_title)

    if not description:
        reason = (clip_context or {}).get('reason') or 'Melhor momento selecionado pela IA.'
        description = str(reason)

    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
    else:
        tags = [str(tag).strip() for tag in tags if str(tag).strip()]

    if not tags:
        tags = ['futebol', 'cortes', 'shorts']

    return {
        'title': title[:100],
        'description': description,
        'tags': tags,
    }


def generate_metadata(clip_context: dict, anthropic_client=None) -> dict:
    """Gera {'title', 'description', 'tags'} para um clip."""
    try:
        if anthropic_client is None:
            import anthropic
            anthropic_client = anthropic.Anthropic()

        prompt = (
            f"Título original: {clip_context.get('source_title', '')}\n"
            f"Motivo do corte: {clip_context.get('reason', '')}\n"
            f"Score viral: {clip_context.get('score', '')}\n"
            f"Intervalo: {clip_context.get('start_time', '')}s até {clip_context.get('end_time', '')}s\n"
            f"Trecho da transcrição:\n{clip_context.get('transcript_excerpt', '')}\n\n"
            "Retorne title, description e tags otimizados para YouTube Shorts."
        )

        response = anthropic_client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': prompt}],
            output_config=METADATA_OUTPUT_SCHEMA,
        )
        data = json.loads(response.content[0].text)
        return _normalize_metadata(data, clip_context)

    except Exception as exc:
        _log(f'Erro ao gerar metadata via Claude: {exc}')
        fallback_title = clip_context.get('source_title') or clip_context.get('reason') or 'Corte de futebol'
        return _normalize_metadata({
            'title': fallback_title,
            'description': clip_context.get('reason') or 'Melhor momento selecionado automaticamente.',
            'tags': ['futebol', 'cortes', 'shorts'],
        }, clip_context)


def append_credits(description: str, credit_template: str, channel_handle: str) -> str:
    """Adiciona linha de créditos ao final da descrição.

    Nunca sobrescreve conteúdo existente.
    Retorna descrição sem modificação se template ou handle estiverem vazios.
    """
    if not credit_template or not channel_handle:
        return description
    credits_line = credit_template.format(channel_handle=channel_handle)
    return f'{description}\n\n{credits_line}'


def update_clip_metadata(conn, clip_id: int, metadata: dict) -> None:
    """Persiste metadata em generated_clips."""
    normalized = _normalize_metadata(metadata)
    tags_text = ','.join(normalized['tags'])

    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips '
            'SET title=%s, description=%s, tags=%s '
            'WHERE id=%s',
            (normalized['title'], normalized['description'], tags_text, clip_id),
        )
    conn.commit()
