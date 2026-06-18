"""
selector.py — Seleção de momentos via Claude Haiku e inserção em generated_clips.

Exporta:
  - select_moments(transcript, anthropic_client=None) -> list[dict]
  - insert_selected_moments(conn, source_video_id, video_id, moments) -> int

Convenções:
  - anthropic_client=None cria cliente de produção; injetado em testes
  - conn: quem chama é responsável por fechar
  - Score >= 7: insere em generated_clips com status 'pending_cut'
  - Score < 7: loga e descarta (não persiste)
"""
import json
from datetime import datetime


SYSTEM_PROMPT = (
    "Você é um especialista em identificar momentos virais de vídeos de futebol e podcasts. "
    "Analise a transcrição fornecida e identifique os melhores segmentos para criar clips de 5 a 10 minutos. "
    "Para futebol: priorize análise tática, debate acalorado, reação a gol, revelação de bastidores. "
    "Para podcasts: priorize discussão intensa, revelação importante, momento de conflito ou humor. "
    "Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente "
    "(10 = viral garantido, 1 = sem valor). "
    "Considere apenas momentos onde o conteúdo é coeso e completo dentro do intervalo de 5-10 minutos."
)

MOMENT_OUTPUT_SCHEMA = {
    'format': {
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'moments': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'start_time': {'type': 'number'},
                            'end_time': {'type': 'number'},
                            'score': {'type': 'number'},
                            'reason': {'type': 'string'},
                        },
                        'required': ['start_time', 'end_time', 'score', 'reason'],
                        'additionalProperties': False,
                    },
                }
            },
            'required': ['moments'],
            'additionalProperties': False,
        },
    }
}


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}')


def _remove_overlaps(moments: list[dict]) -> list[dict]:
    """Remove momentos sobrepostos, mantendo o de maior score.

    Ordena por score decrescente e descarta candidatos que se sobreponham
    a algum momento já selecionado. Retorna no máximo 3 momentos.
    """
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
    """Analisa transcrição com Claude Haiku e retorna momentos selecionados.

    Args:
        transcript: dict com {'video_id', 'text', 'segments'} — output de transcribe_video()
        anthropic_client: cliente Anthropic (None = produção, injetado = testes)

    Returns:
        Lista de dicts com {'start_time', 'end_time', 'score', 'reason'}, máx 3, sem overlap
    """
    try:
        if anthropic_client is None:
            import anthropic
            anthropic_client = anthropic.Anthropic()

        # Formatar transcrição com timestamps por segmento
        lines = []
        for seg in transcript.get('segments', []):
            start = int(seg['start'])
            end = int(seg['end'])
            text = seg['text']
            lines.append(f'[{start}s-{end}s] {text}')
        transcript_text = '\n'.join(lines)

        response = anthropic_client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': transcript_text}],
            output_config=MOMENT_OUTPUT_SCHEMA,
        )

        data = json.loads(response.content[0].text)
        moments = data.get('moments', [])

        # Remover overlaps e limitar a 3
        return _remove_overlaps(moments)

    except Exception as e:
        _log(f'Erro ao selecionar momentos: {e}')
        return []


def insert_selected_moments(conn, source_video_id: int, video_id: str, moments: list[dict]) -> int:
    """Filtra e insere momentos com score >= 7 em generated_clips.

    Args:
        conn: conexão pymysql ativa (quem chama é responsável por fechar)
        source_video_id: FK INT para source_videos.id
        video_id: youtube_video_id (para logging)
        moments: lista de dicts com {'start_time', 'end_time', 'score', 'reason'}

    Returns:
        Número de momentos inseridos (score >= 7)
    """
    # Remover overlaps antes de inserir (mantém o de maior score)
    filtered = _remove_overlaps(moments)

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
                '(source_video_id, start_time, end_time, score, reason, status) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (source_video_id, moment['start_time'], moment['end_time'], score, reason, 'pending_cut'),
            )
        conn.commit()
        inserted += 1
        _log(f'Momento inserido (score {score}): {reason}')

    return inserted
