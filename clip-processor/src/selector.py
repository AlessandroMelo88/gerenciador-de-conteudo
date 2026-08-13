"""
selector.py — Seleção de momentos via IA com fallback automático.

Prioridade em produção:
  1. Anthropic Claude Haiku — se ANTHROPIC_API_KEY definida e válida
  2. Groq LLaMA 3.3-70b    — fallback (usa GROQ_API_KEY já presente)

Na prática hoje quem seleciona é o Groq: ANTHROPIC_API_KEY está vazia no
container (config normal de operação), então o caminho 1 nunca roda. Ou seja,
os prompts daqui são lidos pelo llama-3.3-70b-versatile, não pelo Claude —
importa ao calibrar texto de prompt. Groq (inferência, free tier) não tem
relação com Grok (modelo da xAI), que não é usado aqui.
Ver Docs/SISTEMA-IA-SELECAO.md.

Em testes: anthropic_client injetado é usado diretamente (sem fallback).
"""
import json
import os
from datetime import datetime


SYSTEM_PROMPT = (
    "Você é um especialista em identificar momentos virais de vídeos de futebol e podcasts esportivos. "
    "Analise a transcrição fornecida e identifique os melhores segmentos para criar clips CURTOS, "
    "de PREFERÊNCIA entre 30 segundos e 3 minutos (end_time - start_time >= 30 e <= 180 segundos). "
    "NUNCA selecione segmentos com duração inferior a 30 segundos. "
    "O segmento precisa ter ASSUNTO COMPLETO: começo, meio e fim de um mesmo raciocínio — a fala "
    "que introduz o tema, o desenvolvimento e o desfecho ou a conclusão. Em 3 ou 4 segundos não "
    "existe assunto nenhum; um grito de gol, uma interjeição ou uma frase solta fora de contexto "
    "NÃO servem. Se o raciocínio interessante começa antes do trecho que você escolheria, comece "
    "o segmento onde o tema é introduzido, mesmo que isso o deixe mais longo. "
    "Para futebol: priorize análise tática, debate acalorado, revelação de bastidores e o COMENTÁRIO "
    "sobre um gol (a leitura do que aconteceu) — nunca o instante da narração do gol isolado. "
    "Para podcasts: priorize discussão intensa, revelação importante, momento de conflito ou humor. "
    "Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente "
    "(10 = viral garantido, 1 = sem valor). "
    "Responda APENAS com JSON válido, sem texto adicional:\n"
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>"}]}'
)

# Modo 'longo' (Processar Vídeo > formato=longo): 1 segmento contínuo de 7-20min
# em vez de vários momentos curtos. Prompt separado porque o modelo (testado com
# Groq Llama 3.3-70b) ignora instruções de duração longa quando misturado com o
# pedido de "múltiplos momentos curtos" do modo padrão.
LONG_SYSTEM_PROMPT = (
    "Você é um especialista em identificar o melhor segmento de ANÁLISE ou ENTREVISTA longa "
    "de um vídeo de futebol/esportes para virar um vídeo único no YouTube (não um short). "
    "Analise a transcrição e identifique O MELHOR segmento CONTÍNUO — não fragmente em vários "
    "pedaços — com duração de PREFERÊNCIA ENTRE 420 e 1200 segundos (7 a 20 minutos). "
    "Priorize um raciocínio completo: uma análise tática do início ao fim, uma resposta longa e "
    "coesa de um entrevistado, ou um debate que se desenvolve com começo, meio e fim. Se o "
    "raciocínio natural passar de 20 minutos, pode estender até o ponto em que ele realmente "
    "termina — não corte no meio de uma ideia só pra caber na janela preferida. Não escolha um "
    "trecho curto — o segmento PRECISA ter pelo menos 420 segundos de duração "
    "(end_time - start_time >= 420). "
    "Retorne exatamente 1 momento, com score de 1 a 10 "
    "(10 = análise excelente pra virar vídeo, 1 = sem valor). "
    "Responda APENAS com JSON válido, sem texto adicional:\n"
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>"}]}'
)

# 30s, não 15s: em 3-4 segundos não há assunto, e mesmo 15s não fecha raciocínio.
# Mudar essa constante sozinha não basta — o SYSTEM_PROMPT precisa pedir segmento
# com começo/meio/fim, senão o modelo entrega 30s picados só pra bater a régua.
MIN_SHORTFORM_SECONDS = 30
MAX_SHORTFORM_SECONDS = 180

MIN_LONGFORM_SECONDS = 420
MAX_LONGFORM_SECONDS = 1200


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}', flush=True)


def _normalize_scores(moments: list[dict]) -> list[dict]:
    """Converte scores 0–1 (comum no Groq) para escala 0–10 do pipeline."""
    if not moments:
        return moments
    try:
        scores = [float(m.get('score', 0) or 0) for m in moments]
    except (TypeError, ValueError):
        return moments
    if scores and max(scores) <= 1.0:
        _log('[SELECTOR] Scores em escala 0–1 detectados — normalizando ×10')
        for moment in moments:
            try:
                moment['score'] = float(moment.get('score', 0) or 0) * 10
            except (TypeError, ValueError):
                moment['score'] = 0
    return moments


def _parse_moments(raw_text: str) -> list[dict]:
    """Parse JSON text → lista de dicts de momentos."""
    data = json.loads(raw_text)
    return _normalize_scores(data.get('moments', []))


def _select_via_anthropic_client(client, transcript_text: str, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    """Usa cliente Anthropic já instanciado (produção ou mock de teste)."""
    response = client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=2048,
        system=system_prompt,
        messages=[{'role': 'user', 'content': transcript_text}],
    )
    return _parse_moments(response.content[0].text)


def _select_via_groq(transcript_text: str, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    """Seleciona momentos via Groq LLaMA 3.3-70b (fallback sempre disponível)."""
    from groq import Groq
    client = Groq()
    _log('[SELECTOR] Usando Groq LLaMA 3.3-70b')
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': transcript_text},
        ],
        response_format={'type': 'json_object'},
        temperature=0.3,
        max_tokens=2048,
    )
    return _parse_moments(response.choices[0].message.content)


def _remove_overlaps(moments: list[dict], max_count: int = 3) -> list[dict]:
    """Remove momentos sobrepostos, mantendo o de maior score. Retorna no máximo max_count."""
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
        if len(selected) >= max_count:
            break
    return selected


def _enforce_longform_duration(moments: list[dict], transcript_duration: float) -> list[dict]:
    """Garante duração mínima de MIN_LONGFORM_SECONDS para o modo 'longo'.

    O modelo (mesmo instruído) às vezes devolve segmentos curtos — em vez de
    descartar, estica o segmento simetricamente até o mínimo, respeitando os
    limites da transcrição e o teto de MAX_LONGFORM_SECONDS.
    """
    adjusted = []
    for m in moments:
        duration = m['end_time'] - m['start_time']
        if duration >= MIN_LONGFORM_SECONDS:
            adjusted.append(m)
            continue

        target = min(MIN_LONGFORM_SECONDS, transcript_duration) if transcript_duration else MIN_LONGFORM_SECONDS
        missing = target - duration
        new_start = max(0, m['start_time'] - missing / 2)
        new_end = new_start + target
        if transcript_duration and new_end > transcript_duration:
            new_end = transcript_duration
            new_start = max(0, new_end - target)

        m = dict(m)
        m['start_time'] = new_start
        m['end_time'] = min(new_end, new_start + MAX_LONGFORM_SECONDS)
        adjusted.append(m)
    return adjusted


def _filter_shortform_duration(moments: list[dict]) -> list[dict]:
    """Descarta momentos do formato 'curto' com duração inferior a MIN_SHORTFORM_SECONDS (30s)
    ou superior a MAX_SHORTFORM_SECONDS (180s).

    Descarta em vez de esticar (ao contrário de `_enforce_longform_duration`): trecho
    de 3s esticado pra 30s não vira assunto, só pega 27s de contexto aleatório em volta.
    """
    valid = []
    for m in moments:
        duration = float(m.get('end_time', 0)) - float(m.get('start_time', 0))
        if duration < MIN_SHORTFORM_SECONDS:
            _log(f'[SELECTOR] Momento descartado: duração {duration:.1f}s menor que o mínimo ({MIN_SHORTFORM_SECONDS}s)')
            continue
        if duration > MAX_SHORTFORM_SECONDS:
            _log(f'[SELECTOR] Momento descartado: duração {duration:.1f}s maior que o máximo ({MAX_SHORTFORM_SECONDS}s)')
            continue
        valid.append(m)
    return valid


def select_moments(transcript: dict, anthropic_client=None, fmt: str = 'curto') -> list[dict]:
    """Analisa transcrição e retorna momentos selecionados via IA.

    Fluxo de seleção de provider:
      - Se anthropic_client injetado (testes): usa diretamente, sem fallback.
      - Senão, tenta em ordem:
          1. Anthropic Claude Haiku  (ANTHROPIC_API_KEY configurada e com crédito)
          2. Groq LLaMA 3.3-70b     (GROQ_API_KEY — sempre disponível como fallback)

    Args:
        transcript: dict com {'video_id', 'text', 'segments'} — output de transcribe_video()
        anthropic_client: cliente Anthropic injetado para testes (None = modo produção)
        fmt: 'curto' (vários momentos de 30s-3min, padrão) ou 'longo' (1 segmento
             contínuo de 7-20min — usado pelo Processar Vídeo manual)

    Returns:
        Lista de dicts com {'start_time', 'end_time', 'score', 'reason'}, sem overlap.
    """
    is_longo = fmt == 'longo'
    system_prompt = LONG_SYSTEM_PROMPT if is_longo else SYSTEM_PROMPT
    max_moments = 1 if is_longo else 3

    lines = []
    for seg in transcript.get('segments', []):
        start = int(seg['start'])
        end = int(seg['end'])
        lines.append(f'[{start}s-{end}s] {seg["text"]}')
    transcript_text = '\n'.join(lines)

    segments = transcript.get('segments', [])
    transcript_duration = float(segments[-1]['end']) if segments else 0.0

    # Groq free tier: ~12k TPM. Modo curto trunca bem cedo (~8k chars); modo longo
    # precisa "ver" o vídeo inteiro pra achar um segmento de 7-20min, então usa
    # um teto bem maior antes de truncar.
    MAX_CHARS = 20000 if is_longo else 8000
    if len(transcript_text) > MAX_CHARS:
        transcript_text = transcript_text[:MAX_CHARS]
        _log(f'[SELECTOR] Transcrição truncada para {MAX_CHARS} chars (original maior)')

    if not transcript_text.strip():
        _log('[SELECTOR] Transcrição vazia — sem momentos')
        return []

    def _finalize(moments: list[dict]) -> list[dict]:
        result = _remove_overlaps(moments, max_count=max_moments)
        if is_longo:
            result = _enforce_longform_duration(result, transcript_duration)
        else:
            result = _filter_shortform_duration(result)
        return result

    # Caminho de testes: cliente injetado diretamente
    if anthropic_client is not None:
        try:
            return _finalize(_select_via_anthropic_client(anthropic_client, transcript_text, system_prompt))
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
            moments = _select_via_anthropic_client(client, transcript_text, system_prompt)
            return _finalize(moments)
        except Exception as e:
            _log(f'[SELECTOR] Anthropic indisponível ({e}) — fallback para Groq')
    else:
        _log('[SELECTOR] ANTHROPIC_API_KEY ausente — usando Groq LLaMA diretamente')

    try:
        return _finalize(_select_via_groq(transcript_text, system_prompt))
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
