"""
metadata_generator.py — Geração de metadata e chamada de thumbnail para YouTube.

Exporta:
  - generate_metadata(clip_context, anthropic_client=None) -> dict
  - generate_thumbnail_text(clip_context, anthropic_client=None) -> str
  - update_clip_metadata(conn, clip_id, metadata) -> None
  - append_credits(description, credit_template, channel_handle) -> str

Convenções:
  - anthropic_client=None usa o provider definido pela configuração; clientes são injetados em testes
  - title deve respeitar o limite de 100 caracteres do YouTube
  - tags são persistidas em generated_clips.tags como texto
  - thumbnail_text é gerada em uma chamada dedicada e não é persistida
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime
from typing import Literal

from src.fact_check_prompt import METADATA_FACT_CHECK_INSTRUCTION
from src.metadata_safety import (
    YOUTUBE_DESCRIPTION_MAX_BYTES,
    YOUTUBE_METADATA_SAFETY_INSTRUCTION,
    YOUTUBE_TAGS_MAX_CHARS,
    contains_strong_profanity,
    sanitize_youtube_text,
    validate_youtube_metadata,
    youtube_tags_character_count,
)
from src.prompt_profiles import profile_prompt

GROQ_CHAT_MODEL = (
    os.environ.get('GROQ_CHAT_MODEL') or os.environ.get('GROQ_MODEL') or 'openai/gpt-oss-20b'
)
GROQ_REASONING_EFFORT: Literal['low'] = 'low'


def _configured_ai_provider() -> str:
    return os.environ.get('AI_PROVIDER', 'groq').strip().lower()


THUMBNAIL_TEXT_MAX_CHARS = 64
THUMBNAIL_TEXT_MIN_WORDS = 2
THUMBNAIL_TEXT_MAX_WORDS = 10
TITLE_MAX_CHARS = 100
MAX_GENERATED_DESCRIPTION_CHARS = 3500
MAX_GENERATED_DESCRIPTION_BYTES = 4500
FORBIDDEN_TITLE_LABEL_RE = re.compile(r'\b(?:video\s+longo|long\s+video|shorts?|cortes?|\d+\s*s)\b')
HACKER_LIBERTARIO_NICHE = 'hacker-libertario'
HACKER_CHANNEL_NAME = 'Hacker Libertário'
HACKER_CHANNEL_KEYWORDS = (
    'hacker libertário',
    'cultura hacker',
    'inteligência artificial',
    'IA',
    'Linux',
    'open source',
    'programação',
    'software livre',
    'privacidade digital',
    'soberania digital',
    'segurança digital',
    'automação',
    'desenvolvimento de software',
)
HACKER_CHANNEL_KEYWORDS_HINT = ', '.join(HACKER_CHANNEL_KEYWORDS)

HACKER_CHANNEL_SEO_INSTRUCTION = (
    f'IDENTIDADE DO CANAL: {HACKER_CHANNEL_NAME} publica cortes sobre tecnologia, inteligência '
    'artificial, Linux, open source, programação, privacidade, criptografia e cultura hacker libertária. '
    'PERSPECTIVA EDITORIAL: use a visão crítica e libertária do canal sem trocar fatos por rótulos. '
    'Preserve nomes próprios, produtos, siglas, termos técnicos, categorias legais, citações e expressões de busca específicas. '
    'Não substitua termos do assunto por sinônimos ideológicos que mudem seu sentido ou apaguem a consulta que o público usa. '
    'Apresente juízos libertários como análise ou opinião, não como verificação factual. '
    'O foco do canal é tecnologia, privacidade, código, Bitcoin e liberdade individual; descarte politicagem que não seja parte do assunto tecnológico. '
    'SEO: use uma expressão de busca específica que corresponda ao assunto realmente falado; '
    'coloque-a naturalmente no título e nas primeiras frases da descrição, sem repetir palavras-chave. '
    'Abra a descrição com 1 ou 2 frases que resumam o insight e deixem claro qual problema, ferramenta '
    'ou ideia está em foco; desenvolva o contexto com informações presentes na transcrição e mantenha '
    'a descrição editorial abaixo de 3.500 caracteres. Não prometa alcance ou viralização. Finalize '
    f'com um CTA curto para inscrição no canal {HACKER_CHANNEL_NAME} e, quando fizer sentido, no '
    'máximo 3 hashtags relevantes. '
    f'Use como referências de busca, somente quando forem relevantes: {HACKER_CHANNEL_KEYWORDS_HINT}. '
    'As tags devem ser uma mistura de termos amplos e específicos do trecho, sem #, sem duplicatas e '
    'sem palavras-chave desconectadas do conteúdo. Não inclua créditos: o sistema acrescenta essa linha depois.'
)

METADATA_EDITORIAL_INSTRUCTION = (
    'REGRAS EDITORIAIS OBRIGATÓRIAS: crie um título editorial novo, específico e atraente, '
    'baseado na ideia central, na afirmação ou na conclusão do trecho. O campo "Título original" '
    'serve apenas como contexto para identificar o vídeo: nunca copie, repita ou use esse título '
    'como título final. Por exemplo, se o título original for "FABIO AKITA - Flow #588", não '
    'retorne "FABIO AKITA - Flow #588"; escreva um título que explique o insight principal do '
    'trecho. Use no título e nas primeiras frases da descrição uma expressão de busca específica '
    'do assunto falado, naturalmente e sem repetição artificial. A descrição deve ser completa e '
    'boa para SEO, em PT-BR, com contexto, assunto, '
    'argumentos e conclusão do trecho, explicando claramente por que ele é relevante; não apenas '
    'repita o título ou o motivo do corte. Use somente informações presentes na transcrição e no '
    'contexto fornecido, sem inventar fatos. Nunca inclua rótulos genéricos de formato ou duração '
    'no título, como "Vídeo longo", "Video longo", "Shorts", "corte" ou "30s": isso desperdiça '
    'palavras que devem vender o assunto. Não diga que o vídeo é longo; use esse espaço para a '
    'revelação, conflito ou pergunta que faz a pessoa querer assistir até o fim. Não inclua uma '
    'linha de créditos: ela será acrescentada pelo sistema. Nunca escreva dois sinais "@" consecutivos.'
)

SYSTEM_PROMPT = (
    'Você é especialista em SEO para YouTube Shorts no nicho de futebol brasileiro. '
    'Gere metadados chamativos, claros e honestos para um corte curto. '
    'O título deve ter no máximo 100 caracteres. '
    'A descrição deve resumir o momento e incluir contexto para retenção. '
    'As tags devem ser termos curtos em PT-BR, sem hashtag, focados em futebol, cortes e tema do vídeo. '
    + METADATA_EDITORIAL_INSTRUCTION
    + METADATA_FACT_CHECK_INSTRUCTION
)

LONG_SYSTEM_PROMPT = (
    'Você é especialista em SEO para vídeos longos no YouTube no nicho de futebol brasileiro. '
    'Gere metadados chamativos, claros e honestos para um vídeo horizontal contínuo. '
    'O título deve ter no máximo 100 caracteres. A descrição deve resumir o assunto completo '
    'e incluir contexto para retenção. As tags devem ser termos curtos em PT-BR, sem hashtag, '
    'focados no tema do vídeo e em análise; não use os termos Shorts ou cortes. '
    + METADATA_EDITORIAL_INSTRUCTION
    + METADATA_FACT_CHECK_INSTRUCTION
)

HACKER_LIBERTARIO_SYSTEM_PROMPT = (
    'Você é especialista em SEO para YouTube Shorts e vídeos no nicho de Tecnologia, Inteligência Artificial, Linux, Open Source, Programação e Cultura Hacker Libertária. '
    'Gere metadados chamativos, claros e honestos para o corte. '
    'O título deve ter no máximo 100 caracteres. '
    'A descrição deve resumir o momento e incluir contexto para retenção. '
    'As tags devem ser termos curtos em PT-BR e técnicos, sem hashtag, focados em IA, Linux, Open Source, programação, tecnologia, cortes e tema do vídeo. '
    + HACKER_CHANNEL_SEO_INSTRUCTION
    + METADATA_EDITORIAL_INSTRUCTION
    + METADATA_FACT_CHECK_INSTRUCTION
)

HACKER_LIBERTARIO_LONG_SYSTEM_PROMPT = (
    'Você é especialista em SEO para vídeos longos no YouTube no nicho de Tecnologia, '
    'Inteligência Artificial, Linux, Open Source, Programação e Cultura Hacker Libertária. '
    'Gere metadados chamativos, claros e honestos para um vídeo horizontal contínuo. '
    'O título deve ter no máximo 100 caracteres. A descrição deve resumir o assunto completo '
    'e incluir contexto para retenção. As tags devem ser termos técnicos curtos em PT-BR, sem '
    'hashtag, focados em IA, Linux, Open Source, programação e tecnologia; não use os termos '
    'Shorts ou cortes.'
    + HACKER_CHANNEL_SEO_INSTRUCTION
    + METADATA_EDITORIAL_INSTRUCTION
    + METADATA_FACT_CHECK_INSTRUCTION
)

GENERIC_SYSTEM_PROMPT = (
    'Você é especialista em SEO para YouTube no nicho configurado. Gere metadados chamativos, '
    'claros e honestos para o assunto real do trecho, sem importar vocabulário, identidade ou '
    'promessas de outro nicho. O título deve ter no máximo 100 caracteres. '
    + METADATA_EDITORIAL_INSTRUCTION
    + METADATA_FACT_CHECK_INSTRUCTION
)

THUMBNAIL_SYSTEM_PROMPT = (
    'Você é diretor de criação e especialista em CTR, copywriting e SEO para thumbnails do YouTube. '
    'Sua única tarefa é escolher a melhor chamada textual para a imagem deste corte. '
    'A chamada precisa ser curta, forte, curiosa e capaz de gerar clique, priorizando conflito, '
    'contradição, revelação, pergunta ou afirmação inesperada. Use o contexto e o nicho apenas '
    'para entender o impacto; a chamada deve sair exclusivamente da transcrição. '
    'Escolha uma sequência contínua de palavras realmente dita no trecho, preservando a fala e sem '
    'inventar, parafrasear, intensificar, completar ou atribuir uma acusação ao autor. '
    'Retire somente o contexto explicativo ao selecionar o fragmento, nunca altere o sentido. '
    'Use de 2 a 10 palavras e no máximo 64 caracteres. Não gere título, descrição, tags, hashtags '
    'ou alternativas. Retorne somente um JSON com thumbnail_text.'
)


POLITICA_METADATA_PROMPT = (
    'Você é especialista em SEO para YouTube Shorts e Reels de POLÍTICA e DEBATES. '
    'Gere metadados específicos e fiéis ao trecho: o título (máximo 100 caracteres) deve nomear '
    'naturalmente o tema ou a questão debatida e despertar curiosidade sem exagerar ou atribuir '
    'uma conclusão não dita. A descrição deve resumir a fala e seu contexto. Use somente tags '
    'relacionadas ao tema realmente discutido; não acrescente termos genéricos só para ampliar alcance.'
)


def get_system_prompt(
    niche: str | None = None,
    fmt: str = 'curto',
    prompt_profile: dict[str, object] | None = None,
) -> str:
    is_longo = fmt == 'longo'
    profile_field = 'metadata_long_prompt' if is_longo else 'metadata_short_prompt'
    profile_instruction = profile_prompt(prompt_profile, profile_field)
    if profile_instruction:
        format_instruction = (
            'O título deve ter no máximo 100 caracteres. Gere metadados para um vídeo horizontal contínuo.'
            if is_longo
            else 'O título deve ter no máximo 100 caracteres. Gere metadados para YouTube Shorts.'
        )
        return (
            f'{profile_instruction}\n{format_instruction}\n'
            f'{METADATA_EDITORIAL_INSTRUCTION}{METADATA_FACT_CHECK_INSTRUCTION}'
        )
    if niche == HACKER_LIBERTARIO_NICHE:
        return HACKER_LIBERTARIO_LONG_SYSTEM_PROMPT if is_longo else HACKER_LIBERTARIO_SYSTEM_PROMPT
    if niche in {'futebol', 'esportes', 'podcast'}:
        return LONG_SYSTEM_PROMPT if is_longo else SYSTEM_PROMPT
    if niche == 'politica':
        return POLITICA_METADATA_PROMPT
    return GENERIC_SYSTEM_PROMPT


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

THUMBNAIL_OUTPUT_SCHEMA = {
    'format': {
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'thumbnail_text': {'type': 'string'},
            },
            'required': ['thumbnail_text'],
            'additionalProperties': False,
        },
    }
}


_FAKE_NEWS_SUFFIX_RE = re.compile(
    r'\s*(?:[|.]\s*)?(?:verificação\s+de\s+)?fake\s+news\s*:\s*'
    r'(?:positivo|negativo|inconclusivo)\s*\.?\s*$',
    re.IGNORECASE,
)
_FAKE_NEWS_LINE_RE = re.compile(
    r'^[ \t]*(?:verificação\s+de\s+)?fake\s+news\s*:\s*'
    r'(?:positivo|negativo|inconclusivo)\s*\.?[ \t]*(?:\n|$)',
    re.IGNORECASE | re.MULTILINE,
)
_FACT_CHECK_BLOCK_RE = re.compile(
    r'(?:^|\n)[ \t]*fact\s+check\s*:\s*(?P<facts>.*?)\s*$',
    re.IGNORECASE | re.DOTALL,
)


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def _strip_fake_news_labels(text: str) -> str:
    text = _FAKE_NEWS_LINE_RE.sub('', text or '')
    return _FAKE_NEWS_SUFFIX_RE.sub('', text).strip()


def _ensure_fake_news_verdict(description: str, clip_context: dict | None) -> str:
    """Remove o rótulo gerado sem pesquisa e sem evidência verificável anexada."""
    fact_check_match = _FACT_CHECK_BLOCK_RE.search(description or '')
    if fact_check_match:
        description = description[: fact_check_match.start()].rstrip()
    return _strip_fake_news_labels(description)


def _truncate_description(value: str, *, max_bytes: int = MAX_GENERATED_DESCRIPTION_BYTES) -> str:
    """Trunca a descrição por caracteres e bytes UTF-8 sem partir palavras."""
    text = '\n'.join(re.sub(r'[ \t]+', ' ', line).strip() for line in str(value or '').splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if len(text) <= MAX_GENERATED_DESCRIPTION_CHARS and len(text.encode('utf-8')) <= max_bytes:
        return text

    prefix = text[:MAX_GENERATED_DESCRIPTION_CHARS]
    ellipsis_bytes = len('…'.encode())
    byte_budget = max(max_bytes - ellipsis_bytes, 0)
    while prefix and len(prefix.encode('utf-8')) > byte_budget:
        prefix = prefix[:-1]

    sentence_end = max(prefix.rfind('. '), prefix.rfind('! '), prefix.rfind('? '))
    if sentence_end >= len(prefix) * 0.7:
        return prefix[: sentence_end + 1].rstrip()

    word_boundary = prefix.rfind(' ')
    if word_boundary >= 0:
        prefix = prefix[:word_boundary]
    return prefix.rstrip(' ,;:-') + ('…' if prefix else '')


def _normalize_for_match(text: str) -> str:
    """Normaliza texto para verificar se a chamada veio da transcrição."""
    decomposed = unicodedata.normalize('NFKD', text or '')
    without_accents = ''.join(char for char in decomposed if not unicodedata.combining(char))
    alphanumeric = ''.join(
        char if char.isalnum() or char.isspace() else ' ' for char in without_accents
    )
    return ' '.join(alphanumeric.casefold().split())


def _trim_thumbnail_text(value: object) -> str:
    """Normaliza espaços e aspas externas sem reescrever a fala escolhida."""
    text = ' '.join(str(value or '').split()).strip()
    text = text.strip('"“”«»').strip("'")
    return text.rstrip(' ,;:-')


def _is_literal_thumbnail_text(text: str, transcript_excerpt: str) -> bool:
    """Garante que a IA não inventou uma chamada que não foi dita no corte."""
    normalized_text = _normalize_for_match(text)
    normalized_excerpt = _normalize_for_match(transcript_excerpt)
    return bool(normalized_text and normalized_excerpt and normalized_text in normalized_excerpt)


def _extract_fallback_thumbnail_text(excerpt: str) -> str:
    """Extrai um trecho literal sem linguagem vulgar para thumbnail quando a IA falha."""
    if not excerpt:
        raise ValueError('A transcrição não oferece uma chamada literal segura para thumbnail')
    words = excerpt.split()

    def _valid_clean_candidate(candidate: str) -> bool:
        return (
            THUMBNAIL_TEXT_MIN_WORDS <= len(candidate.split()) <= THUMBNAIL_TEXT_MAX_WORDS
            and len(candidate) <= THUMBNAIL_TEXT_MAX_CHARS
            and not contains_strong_profanity(candidate)
        )

    # Preserve the established first phrase when it is already safe.
    first_window = _trim_thumbnail_text(' '.join(words[: min(8, len(words))]))
    if not contains_strong_profanity(first_window):
        for count in range(min(8, len(words)), THUMBNAIL_TEXT_MIN_WORDS - 1, -1):
            candidate = _trim_thumbnail_text(' '.join(words[:count]))
            if _valid_clean_candidate(candidate):
                return candidate

    # If the opening phrase contains profanity, prefer another complete sentence.
    sentences = re.split(r'(?<=[.!?])\s+', excerpt.strip())
    for sentence in sentences:
        if contains_strong_profanity(sentence):
            continue
        sentence_words = sentence.split()
        for count in range(min(8, len(sentence_words)), THUMBNAIL_TEXT_MIN_WORDS - 1, -1):
            for start in range(len(sentence_words) - count + 1):
                candidate = _trim_thumbnail_text(' '.join(sentence_words[start : start + count]))
                if _valid_clean_candidate(candidate):
                    return candidate

    # Transcripts without sentence punctuation still get a safe literal scan.
    for count in range(min(8, len(words)), THUMBNAIL_TEXT_MIN_WORDS - 1, -1):
        for start in range(len(words) - count + 1):
            candidate = _trim_thumbnail_text(' '.join(words[start : start + count]))
            if _valid_clean_candidate(candidate):
                return candidate

    raise ValueError('A transcrição não oferece uma chamada literal sem linguagem vulgar forte')


def _safe_json_loads(raw_text: str) -> dict:
    """Carrega JSON de forma defensiva, removendo markdown fences e texto auxiliar."""
    text = (raw_text or '').strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Remove markdown codeblocks ```json ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Tenta encontrar primeiro { até o último }
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return {}


def _is_libertarian_context(context: dict | None) -> bool:
    if not context:
        return False
    niche = str(context.get('niche') or '').lower()
    dest_slug = str(context.get('destination_slug') or '').lower()
    profile = context.get('prompt_profile') or {}
    profile_slug = str(profile.get('slug') or '').lower() if hasattr(profile, 'get') else ''
    return (
        dest_slug == HACKER_LIBERTARIO_NICHE
        or niche == HACKER_LIBERTARIO_NICHE
        or profile_slug == 'conteudo-inteligencia'
    )


def _normalize_thumbnail_text(value: object, clip_context: dict | None = None) -> str:
    """Normaliza e valida a chamada da IA sem inventar texto.

    O modelo pode devolver uma sequência literal válida, mas ligeiramente acima
    dos limites pedidos. Nesse caso, preservamos apenas o maior prefixo de
    palavras que continua dentro dos limites do YouTube e que ainda é literal
    da transcrição. Texto vazio, inventado ou curto demais continua sendo erro.
    """
    context = clip_context or {}
    candidate = _trim_thumbnail_text(value)
    excerpt = str(context.get('transcript_excerpt') or '')

    if not candidate:
        raise ValueError('A IA não retornou thumbnail_text')

    words = candidate.split()
    while len(words) > THUMBNAIL_TEXT_MAX_WORDS or len(' '.join(words)) > THUMBNAIL_TEXT_MAX_CHARS:
        words.pop()
    candidate = _trim_thumbnail_text(' '.join(words))

    word_count = len(candidate.split())
    if (
        not THUMBNAIL_TEXT_MIN_WORDS <= word_count <= THUMBNAIL_TEXT_MAX_WORDS
        or not excerpt
        or not _is_literal_thumbnail_text(candidate, excerpt)
        or contains_strong_profanity(candidate)
    ):
        candidate = _extract_fallback_thumbnail_text(excerpt)

    if contains_strong_profanity(candidate):
        raise ValueError('Metadado bloqueado: thumbnail_text contém linguagem vulgar forte.')

    return candidate


def _clean_editorial_text(value: object) -> str:
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    return _FAKE_NEWS_SUFFIX_RE.sub('', text).strip(' |–—')


def _truncate_title(title: str) -> str:
    """Ajusta título longo no limite do YouTube sem cortar uma palavra."""
    if len(title) <= TITLE_MAX_CHARS:
        return title

    truncated = title[:TITLE_MAX_CHARS].rsplit(' ', 1)[0].rstrip(' |–—')
    return truncated or title[:TITLE_MAX_CHARS]


def _editorial_text_key(value: str) -> str:
    return re.sub(r'\W+', ' ', value.casefold()).strip()


def _is_original_source_title(title: str, clip_context: dict) -> bool:
    source_title = _clean_editorial_text(clip_context.get('source_title'))
    return bool(source_title) and _editorial_text_key(title) == _editorial_text_key(source_title)


def _contains_forbidden_title_label(title: str) -> bool:
    """Detecta rótulos de formato que não agregam informação ao título."""
    normalized = _normalize_for_match(title)
    return bool(FORBIDDEN_TITLE_LABEL_RE.search(normalized))


def _normalize_tags(tags: object) -> list[str]:
    """Limpa, deduplica e limita tags pelo orçamento efetivo da API do YouTube."""
    raw_tags: list[str]
    if isinstance(tags, str):
        raw_tags = tags.split(',')
    else:
        raw_tags = [str(tag) for tag in tags] if isinstance(tags, (list, tuple, set)) else []

    normalized: list[str] = []
    seen = set()
    for raw_tag in raw_tags:
        tag = re.sub(r'\s+', ' ', str(raw_tag)).strip().lstrip('#').strip(' ,;')
        key = _normalize_for_match(tag)
        if not key or key in seen:
            continue
        if youtube_tags_character_count([*normalized, tag]) > YOUTUBE_TAGS_MAX_CHARS:
            continue
        seen.add(key)
        normalized.append(tag)
    return normalized


def _normalize_metadata(metadata: dict, clip_context: dict | None = None) -> dict:
    """Valida e normaliza title, description e tags retornados pela IA."""
    context = clip_context or {}
    title = sanitize_youtube_text(metadata.get('title')).strip()
    description = sanitize_youtube_text(metadata.get('description')).strip()
    tags = metadata.get('tags') or []
    is_longo = context.get('format') == 'longo'

    if not title:
        raise ValueError('A IA não retornou um título para SEO')
    title = _truncate_title(title)
    if _contains_forbidden_title_label(title):
        raise ValueError('O título retornado pela IA contém um rótulo genérico de formato')
    if _is_original_source_title(title, context):
        raise ValueError('A IA repetiu o título original em vez de criar um título editorial')
    if not description:
        raise ValueError('A IA não retornou uma descrição para SEO')

    description = _ensure_fake_news_verdict(description, context)
    description = _truncate_description(description)

    tags = _normalize_tags(tags)

    if is_longo:
        tags = [tag for tag in tags if tag.casefold() not in {'short', 'shorts', 'corte', 'cortes'}]

    if not tags:
        raise ValueError('A IA não retornou tags para SEO')

    validate_youtube_metadata(title=title, description=description, tags=tags)

    return {
        'title': title,
        'description': description,
        'tags': tags,
    }


def _build_prompt(clip_context: dict) -> str:
    is_longo = clip_context.get('format') == 'longo'
    profile_instruction = profile_prompt(
        clip_context.get('prompt_profile'),
        'metadata_long_prompt' if is_longo else 'metadata_short_prompt',
    )
    channel_instruction = profile_instruction or (
        HACKER_CHANNEL_SEO_INSTRUCTION
        if clip_context.get('niche') == HACKER_LIBERTARIO_NICHE
        else ''
    )
    format_instruction = (
        'Formato: vídeo normal horizontal, não Shorts. Não use "shorts" ou "cortes" nas tags.'
        if is_longo
        else 'Formato: vídeo curto/Shorts.'
    )
    output_instruction = (
        'Retorne title, description e tags otimizados para um vídeo normal do YouTube, em JSON '
        'com as chaves title, description e tags (lista de strings).'
        if is_longo
        else 'Retorne title, description e tags otimizados para YouTube Shorts, em JSON com as '
        'chaves title, description e tags (lista de strings).'
    )
    return (
        f'{format_instruction}\n'
        f'{channel_instruction}\n'
        f'{METADATA_EDITORIAL_INSTRUCTION}\n'
        f'{YOUTUBE_METADATA_SAFETY_INSTRUCTION}\n'
        f'Nicho configurado: {clip_context.get("niche", "")}\n'
        f'Título original: {clip_context.get("source_title", "")}\n'
        f'Motivo do corte: {clip_context.get("reason", "")}\n'
        f'Score editorial (não prevê alcance): {clip_context.get("score", "")}\n'
        f'Intervalo: {clip_context.get("start_time", "")}s até {clip_context.get("end_time", "")}s\n'
        f'Trecho da transcrição:\n{clip_context.get("transcript_excerpt", "")}\n\n'
        f'{output_instruction}\n'
        f'{METADATA_FACT_CHECK_INSTRUCTION}'
    )


def _build_thumbnail_prompt(clip_context: dict) -> str:
    """Monta o prompt exclusivo da chamada textual da thumbnail."""
    profile_instruction = profile_prompt(clip_context.get('prompt_profile'), 'thumbnail_prompt')
    profile_context = (
        f'Instrução visual do perfil (use apenas para escolher o tema, sem inventar fala): '
        f'{profile_instruction}\n'
        if profile_instruction
        else ''
    )
    return (
        'Escolha uma única chamada para a thumbnail a partir do trecho abaixo. '
        'Avalie primeiro o que tem mais potencial de clique: tensão, surpresa, contradição, '
        'revelação, pergunta ou opinião forte. A frase precisa funcionar sozinha na imagem, '
        'mas deve permanecer uma sequência contínua e literal da transcrição. '
        'Não use o título, o motivo ou conhecimento externo para completar a frase.\n\n'
        f'Título de referência (não copie): {clip_context.get("source_title", "")}\n'
        f'Motivo do corte (somente contexto): {clip_context.get("reason", "")}\n'
        f'Score editorial (não prevê alcance): {clip_context.get("score", "")}\n'
        f'Formato: {clip_context.get("format", "curto")}\n'
        f'{profile_context}'
        f'{YOUTUBE_METADATA_SAFETY_INSTRUCTION}\n'
        f'Trecho da transcrição:\n{clip_context.get("transcript_excerpt", "")}\n\n'
        'Responda exclusivamente com JSON no formato '
        '{"thumbnail_text": "frase literal escolhida"}. '
        'Não inclua explicações, aspas externas, título, descrição, tags ou alternativas.'
    )


def _get_thumbnail_system_prompt(clip_context: dict) -> str:
    profile_instruction = profile_prompt(clip_context.get('prompt_profile'), 'thumbnail_prompt')
    if profile_instruction:
        return (
            f'{THUMBNAIL_SYSTEM_PROMPT}\n{profile_instruction}\n'
            f'{YOUTUBE_METADATA_SAFETY_INSTRUCTION}'
        )
    niche = str(clip_context.get('niche') or '').strip()
    if not niche:
        return f'{THUMBNAIL_SYSTEM_PROMPT}\n{YOUTUBE_METADATA_SAFETY_INSTRUCTION}'
    return (
        f'{THUMBNAIL_SYSTEM_PROMPT} O nicho de referência deste corte é {niche}.\n'
        f'{YOUTUBE_METADATA_SAFETY_INSTRUCTION}'
    )


def _resolve_system_prompt(clip_context: dict) -> str:
    niche = (clip_context or {}).get('niche', '').lower()
    return POLITICA_METADATA_PROMPT if niche == 'politica' else SYSTEM_PROMPT


def _generate_via_anthropic(clip_context: dict, anthropic_client) -> dict:
    if anthropic_client is None:
        import anthropic

        anthropic_client = anthropic.Anthropic()

    system_prompt = get_system_prompt(
        clip_context.get('niche'),
        clip_context.get('format', 'curto'),
        clip_context.get('prompt_profile'),
    )
    response = anthropic_client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=1024,
        system=system_prompt,
        messages=[{'role': 'user', 'content': _build_prompt(clip_context)}],
        output_config=METADATA_OUTPUT_SCHEMA,
    )
    return _safe_json_loads(response.content[0].text)


def _generate_via_groq(clip_context: dict) -> dict:
    """Gera metadata via o provider Groq configurado."""
    from groq import Groq
    from groq.types.chat import ChatCompletionMessageParam
    from groq.types.chat.completion_create_params import ResponseFormatResponseFormatJsonObject

    client = Groq()
    _log('Gerando metadata via Groq LLM')
    system_prompt = get_system_prompt(
        clip_context.get('niche'),
        clip_context.get('format', 'curto'),
        clip_context.get('prompt_profile'),
    )
    messages: list[ChatCompletionMessageParam] = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': _build_prompt(clip_context)},
    ]
    response_format: ResponseFormatResponseFormatJsonObject = {'type': 'json_object'}
    response = client.chat.completions.create(
        model=GROQ_CHAT_MODEL,
        messages=messages,
        response_format=response_format,
        temperature=0.3,
        max_tokens=2048,
        reasoning_effort=GROQ_REASONING_EFFORT,
    )
    return _safe_json_loads(response.choices[0].message.content or '')


def _generate_thumbnail_via_anthropic(clip_context: dict, anthropic_client) -> dict:
    if anthropic_client is None:
        import anthropic

        anthropic_client = anthropic.Anthropic()

    response = anthropic_client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=128,
        system=_get_thumbnail_system_prompt(clip_context),
        messages=[{'role': 'user', 'content': _build_thumbnail_prompt(clip_context)}],
        output_config=THUMBNAIL_OUTPUT_SCHEMA,
    )
    return _safe_json_loads(response.content[0].text)


def _generate_thumbnail_via_groq(clip_context: dict) -> dict:
    from groq import Groq
    from groq.types.chat import ChatCompletionMessageParam
    from groq.types.chat.completion_create_params import ResponseFormatResponseFormatJsonObject

    client = Groq()
    _log('Gerando chamada da thumbnail com o provider de IA disponível')
    messages: list[ChatCompletionMessageParam] = [
        {'role': 'system', 'content': _get_thumbnail_system_prompt(clip_context)},
        {'role': 'user', 'content': _build_thumbnail_prompt(clip_context)},
    ]
    response_format: ResponseFormatResponseFormatJsonObject = {'type': 'json_object'}
    response = client.chat.completions.create(
        model=GROQ_CHAT_MODEL,
        messages=messages,
        response_format=response_format,
        temperature=0.2,
        max_tokens=512,
        reasoning_effort=GROQ_REASONING_EFFORT,
    )
    return _safe_json_loads(response.choices[0].message.content or '')


def generate_thumbnail_text(clip_context: dict, anthropic_client=None) -> str:
    """Gera e valida a chamada da thumbnail exclusivamente com uma IA dedicada.

    O provider é escolhido pela configuração disponível (ou pelo cliente injetado
    em testes). A chamada não é derivada localmente da transcrição; se o provider
    não retornar uma frase literal dentro dos limites, a exceção sobe para que o
    clip falhe e não seja publicado sem o enriquecimento solicitado.
    """
    if anthropic_client is not None:
        data = _generate_thumbnail_via_anthropic(clip_context, anthropic_client)
        return _normalize_thumbnail_text(data.get('thumbnail_text'), clip_context)

    provider = _configured_ai_provider()
    if provider == 'groq':
        data = _generate_thumbnail_via_groq(clip_context)
    elif provider == 'anthropic':
        if not os.environ.get('ANTHROPIC_API_KEY', '').strip():
            raise RuntimeError('AI_PROVIDER=anthropic exige ANTHROPIC_API_KEY configurada')
        data = _generate_thumbnail_via_anthropic(clip_context, None)
    else:
        raise ValueError(f'AI_PROVIDER inválido: {provider!r}; use groq ou anthropic')
    return _normalize_thumbnail_text(data.get('thumbnail_text'), clip_context)


def generate_metadata(clip_context: dict, anthropic_client=None) -> dict:
    """Gera title, description e tags editoriais para um clip.

    Usa o cliente injetado ou AI_PROVIDER (Groq por padrão; Anthropic somente
    com ativação explícita). A resposta deve
    ser completa e editorial; não existe conteúdo determinístico substituto.
    A chamada da thumbnail é gerada separadamente por
    :func:`generate_thumbnail_text`.
    """
    if anthropic_client is not None:
        data = _generate_via_anthropic(clip_context, anthropic_client)
    elif _configured_ai_provider() == 'groq':
        data = _generate_via_groq(clip_context)
    elif _configured_ai_provider() == 'anthropic':
        if not os.environ.get('ANTHROPIC_API_KEY', '').strip():
            raise RuntimeError('AI_PROVIDER=anthropic exige ANTHROPIC_API_KEY configurada')
        data = _generate_via_anthropic(clip_context, None)
    else:
        provider = _configured_ai_provider()
        raise ValueError(f'AI_PROVIDER inválido: {provider!r}; use groq ou anthropic')
    return _normalize_metadata(data, clip_context)


def append_credits(description: str, credit_template: str, channel_handle: str) -> str:
    """Adiciona linha de créditos ao final da descrição.

    Nunca sobrescreve conteúdo existente.
    Retorna descrição sem modificação se template ou handle estiverem vazios.
    """
    if not credit_template or not channel_handle:
        return description
    credits_line = credit_template.format(channel_handle=channel_handle)
    credits_line = re.sub(r'@{2,}', '@', credits_line)
    separator = '\n\n'
    separator_bytes = len(separator.encode('utf-8'))
    credits_line = _truncate_description(
        credits_line, max_bytes=YOUTUBE_DESCRIPTION_MAX_BYTES - separator_bytes
    )
    description_budget = (
        YOUTUBE_DESCRIPTION_MAX_BYTES - separator_bytes - len(credits_line.encode('utf-8'))
    )
    description = _truncate_description(description, max_bytes=description_budget)
    return f'{description}{separator}{credits_line}' if description else credits_line


def resolve_credit_handle(channel_handle: str | None, channel_name: str | None) -> str:
    """Handle a usar no crédito: prioriza @handle real; cai para o nome do canal
    fonte se o handle não estiver cadastrado em source_channels."""
    return channel_handle or channel_name or ''


def update_clip_metadata(
    conn, clip_id: int, metadata: dict, clip_context: dict | None = None
) -> None:
    """Persiste metadata em generated_clips."""
    normalized = _normalize_metadata(metadata, clip_context)
    tags_text = ','.join(normalized['tags'])

    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips SET title=%s, description=%s, tags=%s WHERE id=%s',
            (normalized['title'], normalized['description'], tags_text, clip_id),
        )
    conn.commit()
