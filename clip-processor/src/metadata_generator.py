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
import os
import re
import unicodedata
from datetime import datetime

TITLE_MAX_CHARS = 100
MAX_GENERATED_DESCRIPTION_CHARS = 3500
MAX_GENERATED_DESCRIPTION_BYTES = 4500
YOUTUBE_DESCRIPTION_MAX_BYTES = 5000
# Rótulos de formato/duração que desperdiçam o espaço do título ("Vídeo longo", "Shorts", "30s").
FORBIDDEN_TITLE_LABEL_RE = re.compile(r'\b(?:video\s+longo|long\s+video|shorts?|cortes?|\d+\s*s)\b')

METADATA_EDITORIAL_INSTRUCTION = (
    ' REGRAS EDITORIAIS OBRIGATÓRIAS: crie um título editorial novo, específico e atraente, '
    'baseado na ideia central, na afirmação ou na conclusão do trecho. O campo "Título original" '
    'serve apenas como contexto: nunca copie, repita ou use esse título como título final. '
    'A descrição deve ser completa e boa para SEO, em PT-BR, com contexto, assunto, argumentos e '
    'conclusão do trecho; não apenas repita o título ou o motivo do corte. Use somente informações '
    'presentes na transcrição e no contexto fornecido, sem inventar fatos. Nunca inclua rótulos '
    'genéricos de formato ou duração no título, como "Vídeo longo", "Shorts", "corte" ou "30s": '
    'use esse espaço para a revelação, o conflito ou a pergunta que faz a pessoa querer assistir. '
    'Não inclua linha de créditos (o sistema a acrescenta) e nunca escreva dois sinais "@" seguidos.'
)


SYSTEM_PROMPT = (
    "Você é especialista em SEO para YouTube Shorts no nicho de futebol brasileiro. "
    "Gere metadados chamativos, claros e honestos para um corte curto. "
    "O título deve ter no máximo 100 caracteres. "
    "A descrição deve resumir o momento e incluir contexto para retenção. "
    "As tags devem ser termos curtos em PT-BR, sem hashtag, focados em futebol, cortes e tema do vídeo."
    + METADATA_EDITORIAL_INSTRUCTION
)

POLITICA_METADATA_PROMPT = (
    "Você é um estrategista de elite em SEO e títulos virais de alta retenção para YouTube Shorts e Reels de POLÍTICA e DEBATES. "
    "Gere metadados de alto impacto e curiosidade para o corte selecionado: "
    "1. Título (máximo 100 caracteres): Crie um título extremamente chamativo com gancho de confronto, revelação ou refutação "
    "(ex: 'VEJA O QUE ELE DISSE QUANDO...', 'NÃO ESPERAVA ESSA RESPOSTA...', 'MOMENTO EM QUE FOI DESMASCARADO...', 'JANTADA HISTÓRICA NO DEBATE!'). "
    "2. Descrição: Resumo rápido do embate ou declaração, provocando a audiência a comentar. "
    "3. Tags: Lista de tags em PT-BR (sem hashtag), incluindo temas como politica, debate, shorts, cortes, noticias e nomes citados."
    + METADATA_EDITORIAL_INSTRUCTION
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


def _normalize_for_match(text: str) -> str:
    """Minúsculas, sem acento nem pontuação — base para comparar títulos e detectar rótulos."""
    decomposed = unicodedata.normalize('NFKD', text or '')
    without_accents = ''.join(char for char in decomposed if not unicodedata.combining(char))
    alphanumeric = ''.join(char if char.isalnum() or char.isspace() else ' ' for char in without_accents)
    return ' '.join(alphanumeric.casefold().split())


def _contains_forbidden_title_label(title: str) -> bool:
    """Detecta rótulos de formato/duração ("Vídeo longo", "Shorts", "30s") que não vendem o assunto."""
    return bool(FORBIDDEN_TITLE_LABEL_RE.search(_normalize_for_match(title)))


def _is_original_source_title(title: str, clip_context: dict) -> bool:
    source_title = _normalize_for_match(str(clip_context.get('source_title') or ''))
    return bool(source_title) and _normalize_for_match(title) == source_title


def _truncate_title(title: str) -> str:
    """Ajusta título acima do limite do YouTube sem cortar uma palavra ao meio."""
    if len(title) <= TITLE_MAX_CHARS:
        return title
    truncated = title[:TITLE_MAX_CHARS].rsplit(' ', 1)[0].rstrip(' |–—')
    return truncated or title[:TITLE_MAX_CHARS]


def _truncate_description(value: str, *, max_bytes: int = MAX_GENERATED_DESCRIPTION_BYTES) -> str:
    """Limita a descrição por caracteres e bytes UTF-8 (limite do YouTube é em bytes), sem partir palavras."""
    text = '\n'.join(re.sub(r'[ \t]+', ' ', line).strip() for line in str(value or '').splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if len(text) <= MAX_GENERATED_DESCRIPTION_CHARS and len(text.encode('utf-8')) <= max_bytes:
        return text

    prefix = text[:MAX_GENERATED_DESCRIPTION_CHARS]
    byte_budget = max(max_bytes - len('…'.encode()), 0)
    while prefix and len(prefix.encode('utf-8')) > byte_budget:
        prefix = prefix[:-1]

    sentence_end = max(prefix.rfind('. '), prefix.rfind('! '), prefix.rfind('? '))
    if sentence_end >= len(prefix) * 0.7:
        return prefix[: sentence_end + 1].rstrip()

    word_boundary = prefix.rfind(' ')
    if word_boundary >= 0:
        prefix = prefix[:word_boundary]
    return prefix.rstrip(' ,;:-') + ('…' if prefix else '')


def _normalize_tags(tags: object) -> list[str]:
    """Limpa (sem #), deduplica sem distinguir acento/caixa e mantém a ordem."""
    if isinstance(tags, str):
        raw_tags = tags.split(',')
    elif isinstance(tags, (list, tuple, set)):
        raw_tags = [str(tag) for tag in tags]
    else:
        raw_tags = []

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in raw_tags:
        tag = re.sub(r'\s+', ' ', str(raw_tag)).strip().lstrip('#').strip(' ,;')
        key = _normalize_for_match(tag)
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    return normalized


def _safe_json_loads(raw_text: str) -> dict:
    """JSON tolerante: aceita cerca markdown (```json) e texto ao redor. Vazio se nada parsear."""
    text = (raw_text or '').strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for pattern in (r'```(?:json)?\s*(\{.*?\})\s*```', r'(\{.*\})'):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    return {}


def _normalize_metadata(metadata: dict, clip_context: dict | None = None, strict: bool = False) -> dict:
    """Normaliza metadata retornada pela IA ou pelo fallback.

    strict=True (saída de IA): campo vazio, título com rótulo genérico de formato ou título
    igual ao do vídeo original levantam ValueError — quem chama tenta o próximo provider
    (Anthropic -> Groq). strict=False (fallback final e update_clip_metadata) nunca rejeita:
    o pipeline não pode ficar sem título.
    """
    context = clip_context or {}
    title = str(metadata.get('title') or '').strip()
    description = str(metadata.get('description') or '').strip()
    tags = _normalize_tags(metadata.get('tags') or [])
    niche = context.get('niche') or 'futebol'

    if strict:
        if not title:
            raise ValueError('A IA não retornou um título')
        if not description:
            raise ValueError('A IA não retornou uma descrição')
        if not tags:
            raise ValueError('A IA não retornou tags')
        if _contains_forbidden_title_label(title):
            raise ValueError('O título retornado pela IA contém um rótulo genérico de formato')
        if _is_original_source_title(title, context):
            raise ValueError('A IA repetiu o título original em vez de criar um título editorial')

    if not title:
        default_name = 'Corte Político' if niche == 'politica' else 'Corte de futebol'
        title = str(context.get('source_title') or default_name)

    if not description:
        description = str(context.get('reason') or 'Melhor momento selecionado pela IA.')

    if not tags:
        tags = ['politica', 'debate', 'cortes', 'shorts', 'noticias'] if niche == 'politica' else ['futebol', 'cortes', 'shorts']

    return {
        'title': _truncate_title(title),
        'description': _truncate_description(description),
        'tags': tags,
    }


def _build_prompt(clip_context: dict) -> str:
    niche = clip_context.get('niche') or 'futebol'
    return (
        f"Nicho: {niche}\n"
        f"Título original: {clip_context.get('source_title', '')}\n"
        f"Motivo do corte: {clip_context.get('reason', '')}\n"
        f"Score viral: {clip_context.get('score', '')}\n"
        f"Intervalo: {clip_context.get('start_time', '')}s até {clip_context.get('end_time', '')}s\n"
        f"Trecho da transcrição:\n{clip_context.get('transcript_excerpt', '')}\n\n"
        "Retorne title, description e tags otimizados para YouTube Shorts, em JSON com as chaves "
        "title, description, tags (lista de strings)."
    )


def _resolve_system_prompt(clip_context: dict) -> str:
    niche = (clip_context or {}).get('niche', '').lower()
    return POLITICA_METADATA_PROMPT if niche == 'politica' else SYSTEM_PROMPT


def _generate_via_anthropic(clip_context: dict, anthropic_client) -> dict:
    if anthropic_client is None:
        import anthropic
        anthropic_client = anthropic.Anthropic()

    system_prompt = _resolve_system_prompt(clip_context)
    response = anthropic_client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=1024,
        system=system_prompt,
        messages=[{'role': 'user', 'content': _build_prompt(clip_context)}],
        output_config=METADATA_OUTPUT_SCHEMA,
    )
    return _safe_json_loads(response.content[0].text)


GROQ_MODEL = os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')

# Mesmo teto do seletor: o free tier do Groq recusa pelo max_tokens PEDIDO quando ele passa
# de 1000 (OTPM), devolvendo 429 antes de chamar o modelo. 1024 passava por pouco do limite.
# Title/description/tags cabem folgado. Ver GROQ_MAX_OUTPUT_TOKENS em selector.py.
GROQ_MAX_OUTPUT_TOKENS = int(os.environ.get('GROQ_MAX_OUTPUT_TOKENS', '1000'))


def _generate_via_groq(clip_context: dict) -> dict:
    """Gera metadata via Groq (fallback sempre disponível)."""
    from groq import Groq
    client = Groq()
    system_prompt = _resolve_system_prompt(clip_context)
    _log(f'Fallback: gerando metadata via Groq LLM ({GROQ_MODEL})')
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': _build_prompt(clip_context)},
        ],
        response_format={'type': 'json_object'},
        temperature=0.3,
        max_tokens=1024,
    )
    return _safe_json_loads(response.choices[0].message.content or '')


def generate_metadata(clip_context: dict, anthropic_client=None) -> dict:
    """Gera {'title', 'description', 'tags'} para um clip.

    Tenta Anthropic primeiro; sem ANTHROPIC_API_KEY ou em erro, cai pro Groq
    (mesmo fallback usado pelo seletor de momentos). Só usa o título bruto do
    vídeo como último recurso se as duas IAs falharem.
    """
    try:
        data = _generate_via_anthropic(clip_context, anthropic_client)
        return _normalize_metadata(data, clip_context, strict=True)
    except Exception as exc:
        _log(f'Erro ao gerar metadata via Claude: {exc}')

    try:
        data = _generate_via_groq(clip_context)
        return _normalize_metadata(data, clip_context, strict=True)
    except Exception as exc:
        _log(f'Erro ao gerar metadata via Groq: {exc}')

    niche = (clip_context or {}).get('niche') or 'futebol'
    default_title = 'Corte Político' if niche == 'politica' else 'Corte de futebol'
    fallback_title = clip_context.get('source_title') or clip_context.get('reason') or default_title
    fallback_tags = ['politica', 'debate', 'cortes', 'shorts', 'noticias'] if niche == 'politica' else ['futebol', 'cortes', 'shorts']
    return _normalize_metadata({
        'title': fallback_title,
        'description': clip_context.get('reason') or 'Melhor momento selecionado automaticamente.',
        'tags': fallback_tags,
    }, clip_context)


def append_credits(description: str, credit_template: str, channel_handle: str) -> str:
    """Adiciona linha de créditos ao final da descrição.

    Nunca sobrescreve conteúdo existente.
    Retorna descrição sem modificação se template ou handle estiverem vazios.
    """
    if not credit_template or not channel_handle:
        return description
    credits_line = credit_template.format(channel_handle=channel_handle)
    # Template "@{channel_handle}" com handle já iniciado em "@" gerava "@@canal".
    credits_line = re.sub(r'@{2,}', '@', credits_line)
    separator = '\n\n'
    # Descrição do YouTube tem teto em bytes: a linha de créditos tem prioridade,
    # o corpo é encurtado para caber junto dela.
    credits_line = _truncate_description(
        credits_line, max_bytes=YOUTUBE_DESCRIPTION_MAX_BYTES - len(separator)
    )
    budget = YOUTUBE_DESCRIPTION_MAX_BYTES - len(separator) - len(credits_line.encode('utf-8'))
    if len(description.encode('utf-8')) > budget:
        description = _truncate_description(description, max_bytes=budget)
    return f'{description}{separator}{credits_line}' if description else credits_line


def resolve_credit_handle(channel_handle: str | None, channel_name: str | None) -> str:
    """Handle a usar no crédito: prioriza @handle real; cai para o nome do canal
    fonte se o handle não estiver cadastrado em source_channels."""
    return channel_handle or channel_name or ''


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
