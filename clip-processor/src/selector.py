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

from src.fact_check_prompt import FACT_CHECK_INSTRUCTION, FAKE_NEWS_STATUSES

CONTENT_SELECTION_RULES = (
    'REGRA OBRIGATÓRIA — ANÁLISE AUTÔNOMA DA TRANSCRIÇÃO: leia e interprete todas as linhas '
    'com timestamps da transcrição fornecida antes de escolher qualquer momento. Execute este '
    'processo para cada vídeo, sem assumir posição, duração ou estrutura padrão. Primeiro, '
    'mapeie mentalmente os intervalos comerciais; depois, mapeie os assuntos editoriais completos; '
    'por fim, escolha e valide os melhores candidatos. '
    'Para PUBLICIDADE, detecte semanticamente anúncios, propaganda, patrocínio, merchandising, '
    'product placement, oferta, cupom, código promocional, chamada comercial, link/QR code de venda '
    'ou qualquer CTA de marca. Infira pelos timestamps o início e o fim exatos de cada bloco comercial, '
    'incluindo a transição de entrada e saída, e exclua o bloco inteiro — nunca apenas uma frase. '
    'NÃO use posição fixa, horário fixo ou duração fixa, nem suponha que a propaganda esteja sempre '
    'no começo: cada vídeo pode ter publicidade em pontos e durações diferentes. Uma menção editorial '
    'a uma marca não é publicidade se não houver promoção, venda ou chamada comercial. Nenhum momento '
    'pode sobrepor publicidade, nem por poucos segundos. '
    'Para o ASSUNTO COMPLETO, encontre um único raciocínio com começo, meio e fim: introdução/contexto, '
    'desenvolvimento e conclusão. Infira os limites naturais deste assunto: comece quando a ideia é '
    'apresentada, incluindo a pergunta ou o setup necessário, e termine somente depois da resposta, '
    'desfecho ou conclusão, em uma pausa clara ou troca de assunto. NUNCA corte no meio de uma palavra, '
    'frase, fala, resposta, pergunta, explicação, história, piada ou raciocínio, nem em conjunções ou '
    'preposições ("mas", "porque", "então", "apesar de"). Não force a duração preferida cortando '
    'um assunto: se ele não couber completo e sem publicidade, descarte-o e procure outro. Se não '
    'houver segmento editorial completo e seguro, retorne {"moments": []}. Se aparecer o marcador '
    '[... trecho intermediário omitido ...], trate a lacuna como desconhecida; não atravesse essa lacuna '
    'nem crie um momento que a atravesse. '
)

SYSTEM_PROMPT = (
    'Você é um especialista em identificar momentos virais de vídeos de futebol e podcasts esportivos. '
    'Analise a transcrição fornecida e identifique os melhores segmentos para criar clips CURTOS, '
    'de PREFERÊNCIA entre 30 segundos e 3 minutos (end_time - start_time >= 30 e <= 180 segundos). '
    'Para vídeos curtos (Shorts com duração total menor que 30s), selecione o segmento do vídeo completo. '
    + CONTENT_SELECTION_RULES
    + 'Para futebol: priorize análise tática, debate acalorado, revelação de bastidores e o COMENTÁRIO sobre um gol. '
    'Para podcasts: priorize discussão intensa, revelação importante, momento de conflito ou humor. '
    + FACT_CHECK_INSTRUCTION
    + 'Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente '
    '(10 = viral garantido, 1 = sem valor). '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)

# Modo 'longo' (Processar Vídeo > formato=longo): 1 segmento contínuo de 7-20min
# em vez de vários momentos curtos. Prompt separado porque o modelo (testado com
# Groq Llama 3.3-70b) ignora instruções de duração longa quando misturado com o
# pedido de "múltiplos momentos curtos" do modo padrão.
LONG_SYSTEM_PROMPT = (
    'Você é um especialista em identificar o melhor segmento de ANÁLISE ou ENTREVISTA longa '
    'de um vídeo de futebol/esportes para virar um vídeo único no YouTube (não um short). '
    'Analise a transcrição e identifique O MELHOR segmento CONTÍNUO — não fragmente em vários '
    'pedaços — com duração de PREFERÊNCIA ENTRE 420 e 1200 segundos (7 a 20 minutos). '
    'Priorize um raciocínio completo: uma análise tática do início ao fim, uma resposta longa e '
    'coesa de um entrevistado, ou um debate que se desenvolve com começo, meio e fim. Se o '
    'raciocínio natural passar de 20 minutos, pode estender até o ponto em que ele realmente '
    'termina — não corte no meio de uma ideia só pra caber na janela preferida. Não escolha um '
    'trecho curto — o segmento PRECISA ter pelo menos 420 segundos de duração '
    '(end_time - start_time >= 420). '
    + CONTENT_SELECTION_RULES
    + FACT_CHECK_INSTRUCTION
    + 'Retorne exatamente 1 momento, com score de 1 a 10 '
    '(10 = análise excelente pra virar vídeo, 1 = sem valor). '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)

HACKER_LIBERTARIO_PROMPT = (
    'Você é um especialista em identificar momentos virais, insights profundos e explicações técnicas de alto impacto em vídeos sobre '
    'Inteligência Artificial (IA), Open Source, Linux, Programação, Segurança, Soberania Digital e Filosofia Hacker Libertária (como conteúdos de Fábio Akita, Diolinux, debates tech e cultura hacker). '
    'Analise a transcrição fornecida e identifique os melhores segmentos para criar clips CURTOS, '
    'de PREFERÊNCIA entre 30 segundos e 3 minutos (end_time - start_time >= 30 e <= 180 segundos). '
    'Para vídeos curtos (Shorts com duração total menor que 30s), selecione o segmento do vídeo completo. '
    + CONTENT_SELECTION_RULES
    + 'Priorize: explicações técnicas brilhantes, reflexões sobre liberdade/privacidade digital, analogias marcantes sobre computação/IA, e conselhos diretos de carreira/tecnologia. '
    + FACT_CHECK_INSTRUCTION
    + 'Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente '
    '(10 = viral garantido, 1 = sem valor). '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)

HACKER_LIBERTARIO_LONG_PROMPT = (
    'Você é um especialista em identificar o melhor segmento de ANÁLISE técnica ou ENTREVISTA '
    'de um vídeo sobre Tecnologia, Inteligência Artificial, Linux, Open Source ou Filosofia Hacker '
    'para virar um vídeo único no YouTube (não um short). '
    'Analise a transcrição e identifique O MELHOR segmento CONTÍNUO — não fragmente em vários '
    'pedaços — com duração de PREFERÊNCIA ENTRE 420 e 1200 segundos (7 a 20 minutos). '
    'Priorize um raciocínio completo: uma explicação aprofundada de um conceito de IA/sistemas, '
    'uma reflexão densa sobre soberania tecnológica, ou um debate técnico do início ao fim. '
    + CONTENT_SELECTION_RULES
    + FACT_CHECK_INSTRUCTION
    + 'Retorne exatamente 1 momento, com score de 1 a 10 '
    '(10 = análise excelente pra virar vídeo, 1 = sem valor). '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)


def get_system_prompt(fmt: str = 'curto', niche: str | None = None) -> str:
    is_longo = fmt == 'longo'
    if niche in ('hacker-libertario', 'tecnologia', 'tech', 'linux', 'ia', 'opensource'):
        return HACKER_LIBERTARIO_LONG_PROMPT if is_longo else HACKER_LIBERTARIO_PROMPT
    return LONG_SYSTEM_PROMPT if is_longo else SYSTEM_PROMPT


# 30s, não 15s: em 3-4 segundos não há assunto, e mesmo 15s não fecha raciocínio.
# Mudar essa constante sozinha não basta — o SYSTEM_PROMPT precisa pedir segmento
# com começo/meio/fim, senão o modelo entrega 30s picados só pra bater a régua.
MIN_SHORTFORM_SECONDS = 30
MAX_SHORTFORM_SECONDS = 180

# Whisper/Groq costuma devolver timestamps com arredondamento. Se o modelo
# terminar até este intervalo antes do fim de uma fala, completar o segmento
# evita que o FFmpeg corte a última palavra.
TRANSCRIPT_BOUNDARY_TOLERANCE_SECONDS = 3.0

MIN_LONGFORM_SECONDS = 420
MAX_LONGFORM_SECONDS = 1200

# O modelo precisa de alguma folga para não começar no meio da introdução do
# assunto nem terminar na primeira frase da conclusão. A expansão é limitada
# por pausas da transcrição e pelo teto abaixo para não engolir o tópico seguinte.
LONGFORM_CONTEXT_BEFORE_SECONDS = 12.0
LONGFORM_CONTEXT_AFTER_SECONDS = 24.0
LONGFORM_MAX_CLOSING_EXTENSION_SECONDS = 180.0
LONGFORM_NATURAL_PAUSE_SECONDS = 2.5

# O modo curto retorna até três itens pequenos; manter a resposta compacta deixa
# espaço para a transcrição dentro do limite de TPM do Groq. O modo longo recebe
# um teto próprio maior porque o gpt-oss precisa de tokens de raciocínio antes de
# emitir o único JSON solicitado.
SELECTOR_MAX_OUTPUT_TOKENS = 768
LONGFORM_SELECTOR_MAX_OUTPUT_TOKENS = 2048


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


def _normalize_fake_news_labels(moments: list[dict]) -> list[dict]:
    """Normaliza o rótulo do fact-check e preserva-o no motivo persistido."""
    normalized = []
    for moment in moments:
        item = dict(moment)
        status = str(item.get('fake_news') or '').strip().casefold()
        if status not in FAKE_NEWS_STATUSES:
            normalized.append(item)
            continue

        item['fake_news'] = status
        reason = str(item.get('reason') or '').strip()
        suffix = f'Fake news: {status}'
        if 'fake news:' not in reason.casefold():
            item['reason'] = f'{reason} | {suffix}' if reason else suffix
        normalized.append(item)
    return normalized


def complete_moment_boundaries(
    moments: list[dict], transcript_segments: list[dict] | None
) -> list[dict]:
    """Completa limites próximos das bordas dos segmentos da transcrição.

    Proteções implementadas:
    - start_time: Se cair logo no início de um segmento (<= 3.0s), recua para o início exato da fala.
    - end_time:
      * Se cair muito no início de um novo segmento (ex: <= 2.5s), recua (snap back) para o fim do
        segmento anterior, evitando pegar apenas o começo de uma frase inacabada ("Apesar de...").
      * Se cair no corpo ou perto do fim de um segmento (<= tolerance), avança (snap forward) até o fim
        daquele segmento, completando a frase inteira.
    """
    if not moments or not transcript_segments:
        return moments

    segments = []
    for segment in transcript_segments:
        try:
            segment_start = float(segment['start'])
            segment_end = float(segment['end'])
        except (KeyError, TypeError, ValueError):
            continue
        if segment_end > segment_start:
            segments.append((segment_start, segment_end))

    if not segments:
        return moments

    adjusted = []
    tolerance = TRANSCRIPT_BOUNDARY_TOLERANCE_SECONDS
    for moment in moments:
        try:
            start_time = float(moment['start_time'])
            end_time = float(moment['end_time'])
        except (KeyError, TypeError, ValueError):
            adjusted.append(moment)
            continue

        new_start = start_time
        new_end = end_time

        # Ajuste de início
        for segment_start, segment_end in segments:
            if segment_start <= start_time < segment_end:
                if start_time - segment_start <= tolerance:
                    new_start = segment_start
                break

        # Ajuste de fim
        for seg_idx, (segment_start, segment_end) in enumerate(segments):
            if segment_start < end_time < segment_end:
                # Se o timestamp pegaria apenas os primeiros segundos de um novo segmento (<= 2.5s)
                if (end_time - segment_start) <= 2.5 and seg_idx > 0:
                    prev_end = segments[seg_idx - 1][1]
                    new_end = prev_end
                elif (segment_end - end_time) <= tolerance:
                    new_end = segment_end
                break
            elif abs(end_time - segment_end) <= tolerance:
                new_end = segment_end
                break

        if new_start == start_time and new_end == end_time:
            adjusted.append(moment)
            continue

        updated = dict(moment)
        updated['start_time'] = new_start
        updated['end_time'] = new_end
        _log(
            f'[SELECTOR] Limites ajustados à transcrição: '
            f'{start_time:.2f}-{end_time:.2f}s → {new_start:.2f}-{new_end:.2f}s'
        )
        adjusted.append(updated)

    return adjusted


def expand_longform_context(
    moments: list[dict], transcript_segments: list[dict] | None
) -> list[dict]:
    """Inclui contexto editorial e leva o fim até uma pausa natural.

    A IA recebe uma janela limitada da transcrição e pode devolver um limite
    tecnicamente válido que ainda corta a introdução ou a conclusão. Para o
    vídeo longo, adicionamos uma pequena margem antes e depois. O fim avança
    pelos segmentos contíguos até a primeira pausa perceptível, sem atravessar
    uma troca natural de assunto nem adicionar mais que três minutos.
    """
    if not moments or not transcript_segments:
        return moments

    segments: list[tuple[float, float]] = []
    for segment in transcript_segments:
        try:
            segment_start = float(segment['start'])
            segment_end = float(segment['end'])
        except (KeyError, TypeError, ValueError):
            continue
        if segment_end > segment_start:
            segments.append((segment_start, segment_end))

    if not segments:
        return moments

    segments.sort()
    transcript_end = segments[-1][1]
    expanded: list[dict] = []

    for moment in moments:
        try:
            start_time = float(moment['start_time'])
            end_time = float(moment['end_time'])
        except (KeyError, TypeError, ValueError):
            expanded.append(moment)
            continue

        if end_time <= start_time:
            expanded.append(moment)
            continue

        target_start = max(0.0, start_time - LONGFORM_CONTEXT_BEFORE_SECONDS)
        new_start = target_start
        for segment_start, segment_end in segments:
            if segment_start <= target_start < segment_end:
                new_start = segment_start
                break

        # Começa pelo fim do segmento que contém a borda escolhida. Assim a
        # extensão nunca corta uma fala no meio.
        requested_end = min(end_time, transcript_end)
        current_end = requested_end
        last_segment_index = None
        previous_segment_index = None
        for index, (segment_start, segment_end) in enumerate(segments):
            if segment_start <= requested_end <= segment_end:
                current_end = segment_end
                last_segment_index = index
                break
            if segment_end < requested_end:
                # Guarda o último segmento anterior somente enquanto ainda
                # estamos avançando pela transcrição. Não continue atualizando
                # depois de uma pausa, senão o fim pode voltar para o início
                # do vídeo ao encontrar o primeiro gap.
                previous_segment_index = index
                continue
            if segment_start > requested_end:
                break

        if last_segment_index is None and previous_segment_index is not None:
            previous_end = segments[previous_segment_index][1]
            if previous_end >= start_time:
                last_segment_index = previous_segment_index
                current_end = previous_end

        new_end = current_end
        if last_segment_index is not None:
            original_end = end_time
            cursor = current_end
            extension_limit = max(
                LONGFORM_MAX_CLOSING_EXTENSION_SECONDS,
                LONGFORM_CONTEXT_AFTER_SECONDS,
            )
            for segment_start, segment_end in segments[last_segment_index + 1 :]:
                gap = segment_start - cursor
                if gap >= LONGFORM_NATURAL_PAUSE_SECONDS:
                    break
                if segment_end - original_end > extension_limit:
                    break
                cursor = segment_end
                new_end = cursor

        updated = dict(moment)
        updated['start_time'] = new_start
        updated['end_time'] = min(new_end, transcript_end, new_start + MAX_LONGFORM_SECONDS)
        expanded.append(updated)

    return expanded


def _parse_moments(raw_text: str) -> list[dict]:
    """Parse JSON text → lista de dicts de momentos."""
    data = json.loads(raw_text)
    moments = _normalize_scores(data.get('moments', []))
    return _normalize_fake_news_labels(moments)


def _select_via_anthropic_client(
    client, transcript_text: str, system_prompt: str = SYSTEM_PROMPT
) -> list[dict]:
    """Usa cliente Anthropic já instanciado (produção ou mock de teste)."""
    response = client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=2048,
        system=system_prompt,
        messages=[{'role': 'user', 'content': transcript_text}],
    )
    return _parse_moments(response.content[0].text)


def _select_via_groq(
    transcript_text: str,
    system_prompt: str = SYSTEM_PROMPT,
    *,
    max_tokens: int = SELECTOR_MAX_OUTPUT_TOKENS,
) -> list[dict]:
    """Seleciona momentos via Groq (fallback sempre disponível)."""
    from groq import Groq

    client = Groq()
    _log('[SELECTOR] Usando Groq LLM')
    response = client.chat.completions.create(
        model='openai/gpt-oss-120b',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': transcript_text},
        ],
        response_format={'type': 'json_object'},
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return _parse_moments(response.choices[0].message.content or '')


def _remove_overlaps(moments: list[dict], max_count: int = 3) -> list[dict]:
    """Remove momentos sobrepostos, mantendo o de maior score. Retorna no máximo max_count."""
    sorted_moments = sorted(moments, key=lambda m: m['score'], reverse=True)
    selected: list[dict] = []
    for candidate in sorted_moments:
        overlaps = any(
            not (
                candidate['end_time'] <= kept['start_time']
                or candidate['start_time'] >= kept['end_time']
            )
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
    adjusted: list[dict] = []
    for m in moments:
        duration = m['end_time'] - m['start_time']
        if duration >= MIN_LONGFORM_SECONDS:
            adjusted.append(m)
            continue

        target = (
            min(MIN_LONGFORM_SECONDS, transcript_duration)
            if transcript_duration
            else MIN_LONGFORM_SECONDS
        )
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


def _filter_shortform_duration(
    moments: list[dict], transcript_duration: float | None = None
) -> list[dict]:
    """Descarta momentos do formato 'curto' com duração inferior ao mínimo aceitável
    ou superior a MAX_SHORTFORM_SECONDS (180s).
    """
    valid: list[dict] = []
    min_required: float = MIN_SHORTFORM_SECONDS
    if transcript_duration and transcript_duration > 5:
        min_required = min(MIN_SHORTFORM_SECONDS, transcript_duration - 0.5)

    for m in moments:
        duration = float(m.get('end_time', 0)) - float(m.get('start_time', 0))
        if duration < min_required:
            _log(
                f'[SELECTOR] Momento descartado: duração {duration:.1f}s menor que o mínimo ({min_required:.1f}s)'
            )
            continue
        if duration > MAX_SHORTFORM_SECONDS:
            _log(
                f'[SELECTOR] Momento descartado: duração {duration:.1f}s maior que o máximo ({MAX_SHORTFORM_SECONDS}s)'
            )
            continue
        valid.append(m)
    return valid


def _clamp_moment_bounds(moments: list[dict], transcript_duration: float) -> list[dict]:
    """Mantém limites devolvidos pela IA dentro da duração real da transcrição."""
    if not moments or transcript_duration <= 0:
        return moments

    clamped: list[dict] = []
    for moment in moments:
        try:
            start_time = float(moment['start_time'])
            end_time = float(moment['end_time'])
        except (KeyError, TypeError, ValueError):
            clamped.append(moment)
            continue

        new_start = min(max(start_time, 0.0), transcript_duration)
        new_end = min(max(end_time, 0.0), transcript_duration)
        if new_end < new_start:
            new_end = new_start

        if new_start == start_time and new_end == end_time:
            clamped.append(moment)
            continue

        updated = dict(moment)
        updated['start_time'] = new_start
        updated['end_time'] = new_end
        clamped.append(updated)

    return clamped


def select_moments(
    transcript: dict, anthropic_client=None, fmt: str = 'curto', niche: str | None = None
) -> list[dict]:
    """Analisa transcrição e retorna momentos selecionados via IA.

    Fluxo de seleção de provider:
      - Se anthropic_client injetado (testes): usa diretamente, sem fallback.
      - Senão, tenta em ordem:
          1. Anthropic Claude Haiku  (ANTHROPIC_API_KEY configurada e com crédito)
          2. Groq                    (GROQ_API_KEY — sempre disponível como fallback)

    Args:
        transcript: dict com {'video_id', 'text', 'segments'} — output de transcribe_video()
        anthropic_client: cliente Anthropic injetado para testes (None = modo produção)
        fmt: 'curto' (vários momentos de 30s-3min, padrão) ou 'longo' (1 segmento
             contínuo de 7-20min — usado pelo Processar Vídeo manual)
        niche: slug do nicho (ex: 'hacker-libertario', 'futebol', 'podcast') para calibrar o prompt

    Returns:
        Lista de dicts com {'start_time', 'end_time', 'score', 'reason'}, sem overlap.
    """
    is_longo = fmt == 'longo'
    system_prompt = get_system_prompt(fmt=fmt, niche=niche)
    max_moments = 1 if is_longo else 3

    lines = []
    transcript_duration = 0.0
    for seg in transcript.get('segments', []):
        start = float(seg['start'])
        end = float(seg['end'])
        if end > transcript_duration:
            transcript_duration = end
        lines.append(f'[{int(start)}s-{int(end)}s] {seg["text"]}')
    transcript_text = '\n'.join(lines)

    # Groq free tier: limite efetivo de 8k tokens por minuto contando entrada e
    # saída. O modo longo reserva 2048 tokens para o raciocínio/JSON; por isso
    # mantém uma janela de 14k caracteres, em vez de estourar o TPM com 18k.
    MAX_CHARS = 14000 if is_longo else 8000
    selector_max_tokens = (
        LONGFORM_SELECTOR_MAX_OUTPUT_TOKENS if is_longo else SELECTOR_MAX_OUTPUT_TOKENS
    )
    if len(transcript_text) > MAX_CHARS:
        if is_longo:
            # Preserve o começo (onde a introdução editorial costuma estar) e
            # o fim da janela visível (onde a conclusão pode estar). O marcador
            # impede a IA de inventar um intervalo atravessando o trecho omitido.
            tail_chars = 3_000
            head_chars = MAX_CHARS - tail_chars
            head = transcript_text[:head_chars].rsplit('\n', 1)[0]
            tail = transcript_text[-tail_chars:].split('\n', 1)[-1]
            transcript_text = f'{head}\n[... trecho intermediário omitido ...]\n{tail}'
        else:
            transcript_text = transcript_text[:MAX_CHARS]
        _log(f'[SELECTOR] Transcrição truncada para {MAX_CHARS} chars (original maior)')

    if not transcript_text.strip():
        _log('[SELECTOR] Transcrição vazia — sem momentos')
        return []

    def _finalize(moments: list[dict]) -> list[dict]:
        moments = _clamp_moment_bounds(moments, transcript_duration)
        moments = complete_moment_boundaries(moments, transcript.get('segments', []))
        if is_longo:
            moments = expand_longform_context(moments, transcript.get('segments', []))
        result = _remove_overlaps(moments, max_count=max_moments)
        if is_longo:
            result = _enforce_longform_duration(result, transcript_duration)
            result = _clamp_moment_bounds(result, transcript_duration)
            result = complete_moment_boundaries(result, transcript.get('segments', []))
            result = expand_longform_context(result, transcript.get('segments', []))
            # A resposta do modelo pode apontar além do fim real da transcrição.
            # A expansão então encurta o momento; revalidar a duração aqui evita
            # que um vídeo longo escape com menos de 420s.
            result = _clamp_moment_bounds(result, transcript_duration)
            result = _enforce_longform_duration(result, transcript_duration)
            result = complete_moment_boundaries(result, transcript.get('segments', []))
        else:
            result = _filter_shortform_duration(result)
        return result

    # Caminho de testes: cliente injetado diretamente
    if anthropic_client is not None:
        try:
            return _finalize(
                _select_via_anthropic_client(anthropic_client, transcript_text, system_prompt)
            )
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
        return _finalize(
            _select_via_groq(
                transcript_text,
                system_prompt,
                max_tokens=selector_max_tokens,
            )
        )
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
            'SELECT id FROM destination_channels WHERE niche = %s AND active = TRUE LIMIT 1',
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
                (
                    source_video_id,
                    moment['start_time'],
                    moment['end_time'],
                    score,
                    reason,
                    'pending_cut',
                    destination_channel_id,
                ),
            )
        conn.commit()
        inserted += 1
        _log(f'Momento inserido (score {score}, dest_ch={destination_channel_id}): {reason}')

    return inserted
