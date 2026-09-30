"""Shared guard for risky profanity in YouTube metadata across every channel."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

YOUTUBE_METADATA_SAFETY_INSTRUCTION = (
    'Regra global do YouTube, obrigatória para todos os canais e formatos: não use palavrões '
    'ou linguagem obscena forte no título, na descrição, nas tags, nas hashtags ou no texto da '
    'thumbnail, mesmo quando aparecerem no título original ou na transcrição. Reescreva a ideia '
    'com linguagem neutra e fiel ao conteúdo; não disfarce palavrões com símbolos, asteriscos, '
    'números ou separação de letras. Não use os caracteres ASCII < e > no título ou na descrição; '
    'escreva comparações por extenso e explique marcação HTML ou trechos de código em palavras. '
    'Para a thumbnail, escolha outra frase literal e limpa da '
    'transcrição. Se não houver uma frase segura, não gere metadados para publicação.'
)
YOUTUBE_DESCRIPTION_MAX_BYTES = 5000
YOUTUBE_TAGS_MAX_CHARS = 500

# Roots are limited to unambiguous, stronger profanity commonly found in
# Portuguese and English metadata. Mild expressions stay available.
_PROFANITY_STEMS = (
    'porr',
    'caralh',
    'merd',
    'bost',
    'fod',
    'fud',
    'bucet',
    'bocet',
    'arromb',
    'cuz',
    'desgrac',
    'fuck',
    'shit',
    'bullshit',
    'motherfuck',
    'asshole',
    'bitch',
    'cunt',
    'mierd',
    'jod',
    'krlh',
)
_PROFANITY_WORDS = (
    'puta',
    'putas',
    'puto',
    'putos',
    'putaria',
    'putarias',
    'pqp',
    'fdp',
    'vsf',
    'vtnc',
)
_LEET_EQUIVALENTS = {
    'a': 'a4@',
    'e': 'e3',
    'i': 'i1!',
    'o': 'o0',
    's': 's5$',
    't': 't7',
}


def _ascii_fold(text: str) -> str:
    decomposed = unicodedata.normalize('NFKD', text or '')
    unaccented = ''.join(char for char in decomposed if not unicodedata.combining(char))
    return unaccented.casefold()


def _build_word_pattern(word: str, *, allow_suffix: bool) -> re.Pattern[str]:
    parts = []
    for char in word:
        variants = set(_LEET_EQUIVALENTS.get(char, char))
        variants.add('*')
        alternatives = '|'.join(re.escape(value) for value in sorted(variants))
        parts.append(f'(?:{alternatives})')

    body = r'[^a-z0-9]*'.join(parts)
    suffix = r'[a-z0-9]*' if allow_suffix else ''
    return re.compile(rf'(?<![a-z0-9]){body}{suffix}(?![a-z0-9])')


_COMPILED_PROFANITY_PATTERNS = tuple(
    _build_word_pattern(stem, allow_suffix=True) for stem in _PROFANITY_STEMS
) + tuple(_build_word_pattern(word, allow_suffix=False) for word in _PROFANITY_WORDS)


def contains_strong_profanity(text: object) -> bool:
    """Return whether text contains configured strong profanity or obfuscation."""
    normalized = _ascii_fold(str(text or ''))
    return any(pattern.search(normalized) for pattern in _COMPILED_PROFANITY_PATTERNS)


def sanitize_youtube_text(value: object) -> str:
    """Replace characters excluded by YouTube's title/description API fields."""
    return str(value or '').replace('<', '‹').replace('>', '›')


def youtube_tags_character_count(tags: Iterable[object]) -> int:
    """Count tags using YouTube Data API rules, including spaces and separators."""
    values = [str(tag) for tag in tags if str(tag)]
    tag_chars = sum(len(tag) + (2 if any(char.isspace() for char in tag) else 0) for tag in values)
    return tag_chars + max(len(values) - 1, 0)


def validate_youtube_metadata(
    title: object = '',
    description: object = '',
    tags: str | Iterable[object] | None = None,
) -> None:
    """Raise before persistence or upload if YouTube metadata includes profanity."""
    tag_values = tags.split(',') if isinstance(tags, str) else (tags or ())
    description_text = str(description or '')
    if len(description_text.encode('utf-8')) > YOUTUBE_DESCRIPTION_MAX_BYTES:
        raise ValueError(
            'Metadado bloqueado: descrição excede o limite de '
            f'{YOUTUBE_DESCRIPTION_MAX_BYTES} bytes do YouTube.'
        )
    if youtube_tags_character_count(tag_values) > YOUTUBE_TAGS_MAX_CHARS:
        raise ValueError(
            'Metadado bloqueado: tags excedem o limite de '
            f'{YOUTUBE_TAGS_MAX_CHARS} caracteres efetivos do YouTube.'
        )
    fields = (
        ('título', title),
        ('descrição', description_text),
        ('tags', ' '.join(str(tag) for tag in tag_values)),
    )
    for field, value in fields:
        if field != 'tags' and ('<' in str(value) or '>' in str(value)):
            raise ValueError(
                f'Metadado bloqueado: {field} contém os caracteres < e > não aceitos pelo YouTube.'
            )
        if contains_strong_profanity(value):
            raise ValueError(f'Metadado bloqueado: {field} contém linguagem vulgar forte.')
