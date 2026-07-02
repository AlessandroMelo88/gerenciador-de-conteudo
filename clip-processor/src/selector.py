"""
selector.py — Seleção de momentos via IA com fallback automático.

Prioridade em produção:
  1. Anthropic Claude Haiku — se ANTHROPIC_API_KEY definida e válida
  2. Groq LLaMA 3.3-70b    — fallback (usa GROQ_API_KEY já presente)

Em testes: anthropic_client injetado é usado diretamente (sem fallback).
"""
import json
import os
from datetime import datetime


SYSTEM_PROMPT = (
    "Você é um especialista em identificar momentos virais de vídeos de futebol e podcasts esportivos. "
    "Analise a transcrição fornecida e identifique os melhores segmentos para criar clips de 5 a 10 minutos. "
    "Para futebol: priorize análise tática, debate acalorado, reação a gol, revelação de bastidores. "
    "Para podcasts: priorize discussão intensa, revelação importante, momento de conflito ou humor. "
    "Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente "
    "(10 = viral garantido, 1 = sem valor). "
    "Considere apenas momentos onde o conteúdo é coeso e completo dentro do intervalo de 5-10 minutos.\n\n"
    "Responda APENAS com JSON válido, sem texto adicional:\n"
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>"}]}'
)


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}', flush=True)


def _parse_moments(raw_text: str) -> list[dict]:
    """Parse JSON text → lista de dicts de momentos."""
    data = json.loads(raw_text)
    return data.get('moments', [])


def _select_via_anthropic_client(client, transcript_text: str) -> list[dict]:
    """Usa cliente Anthropic já instanciado (produção ou mock de teste)."""
    response = client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': transcript_text}],
    )
    return _parse_moments(response.content[0].text)


def _select_via_groq(transcript_text: str) -> list[dict]:
    """Seleciona momentos via Groq LLaMA 3.3-70b (fallback sempre disponível)."""
    from groq import Groq
    client = Groq()
    _log('[SELECTOR] Usando Groq LLaMA 3.3-70b')
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': transcript_text},
        ],
        response_format={'type': 'json_object'},
        temperature=0.3,
        max_tokens=2048,
    )
    return _parse_moments(response.choices[0].message.content)


def _remove_overlaps(moments: list[dict]) -> list[dict]:
    """Remove momentos sobrepostos, mantendo o de maior score. Retorna no máximo 3."""
    sorted_moments = sorted(moments, key=lambda m: m['score'], reverse=True)
    selected = []
    for candidate in sorted_moments:
        overlaps = any(
            not (candidate['end_time'] <= kept['start_time'] or
                 candidate['start_time'] >= kept['end_time'])
            for kept in selected
        )
        if not overlaps:
            selected.append(candidate)
        if len(selected) >= 3:
            break
    return selected


def select_moments(transcript: dict, anthropic_client=None) -> list[dict]:
    """Analisa transcrição e retorna momentos selecionados via IA.

    Fluxo de seleção de provider:
      - Se anthropic_client injetado (testes): usa diretamente, sem fallback.
      - Senão, tenta em ordem:
          1. Anthropic Claude Haiku  (ANTHROPIC_API_KEY configurada e com crédito)
          2. Groq LLaMA 3.3-70b     (GROQ_API_KEY — sempre disponível como fallback)

    Args:
        transcript: dict com {'video_id', 'text', 'segments'} — output de transcribe_video()
        anthropic_client: cliente Anthropic injetado para testes (None = modo produção)

    Returns:
        Lista de dicts com {'start_time', 'end_time', 'score', 'reason'}, máx 3, sem overlap
    """
    lines = []
    for seg in transcript.get('segments', []):
        start = int(seg['start'])
        end = int(seg['end'])
        lines.append(f'[{start}s-{end}s] {seg["text"]}')
    transcript_text = '\n'.join(lines)

    # Groq free tier: ~12k TPM — trunca transcrições longas para ~8000 chars (~6k tokens)
    MAX_CHARS = 8000
    if len(transcript_text) > MAX_CHARS:
        transcript_text = transcript_text[:MAX_CHARS]
        _log(f'[SELECTOR] Transcrição truncada para {MAX_CHARS} chars (original maior)')

    if not transcript_text.strip():
        _log('[SELECTOR] Transcrição vazia — sem momentos')
        return []

    # Caminho de testes: cliente injetado diretamente
    if anthropic_client is not None:
        try:
            return _remove_overlaps(_select_via_anthropic_client(anthropic_client, transcript_text))
        except Exception as e:
            _log(f'Erro ao selecionar momentos: {e}')
            return []

    # Produção: tenta Anthropic primeiro, cai para Groq
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            _log('[SELECTOR] Usando Anthropic Claude Haiku')
            moments = _select_via_anthropic_client(client, transcript_text)
            return _remove_overlaps(moments)
        except Exception as e:
            _log(f'[SELECTOR] Anthropic indisponível ({e}) — fallback para Groq')
    else:
        _log('[SELECTOR] ANTHROPIC_API_KEY ausente — usando Groq LLaMA diretamente')

    try:
        return _remove_overlaps(_select_via_groq(transcript_text))
    except Exception as e:
        _log(f'Erro ao selecionar momentos: {e}')
        return []


def _lookup_destination_channel_id(conn, source_video_id: int) -> int | None:
    """Resolve destination_channel_id via JOIN source_videos → source_channels → destination_channels."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT sc.target_niche '
            'FROM source_videos sv '
            'JOIN source_channels sc ON sc.id = sv.channel_id '
            'WHERE sv.id = %s',
            (source_video_id,),
        )
        row = cur.fetchone()

    if not row or not row.get('target_niche'):
        return None

    target_niche = row['target_niche']

    with conn.cursor() as cur:
        cur.execute(
            'SELECT id FROM destination_channels '
            'WHERE niche = %s AND active = TRUE '
            'LIMIT 1',
            (target_niche,),
        )
        dest_row = cur.fetchone()

    return dest_row['id'] if dest_row else None


def insert_selected_moments(conn, source_video_id: int, video_id: str, moments: list[dict]) -> int:
    """Filtra momentos com score >= 7 e insere em generated_clips.

    Returns:
        Número de momentos inseridos.
    """
    filtered = _remove_overlaps(moments)
    destination_channel_id = _lookup_destination_channel_id(conn, source_video_id)

    inserted = 0
    for moment in filtered:
        if inserted >= 3:
            break

        score = moment['score']
        reason = moment['reason']

        if score < 7:
            _log(f'Momento descartado (score {score}): {reason}')
            continue

        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO generated_clips '
                '(source_video_id, start_time, end_time, score, reason, status, destination_channel_id) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (source_video_id, moment['start_time'], moment['end_time'], score, reason,
                 'pending_cut', destination_channel_id),
            )
        conn.commit()
        inserted += 1
        _log(f'Momento inserido (score {score}, dest_ch={destination_channel_id}): {reason}')

    return inserted
