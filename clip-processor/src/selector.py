"""
selector.py — Seleção de momentos via IA com fallback automático.

O provider padrão é Groq com GPT-OSS 20B. Outro provider só é usado quando
AI_PROVIDER o seleciona explicitamente. O texto editorial pode vir de
prompt_profiles; sem perfil, entram as constantes de fallback deste módulo.
Groq (inferência, free tier) não tem relação com Grok (modelo da xAI).
Ver Docs/SISTEMA-IA-SELECAO.md.

Em testes: anthropic_client injetado é usado diretamente (sem fallback).
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from src.db import fetch_used_moments
from src.fact_check_prompt import FACT_CHECK_INSTRUCTION, FAKE_NEWS_STATUSES
from src.media_contract import SHORTS_MAX_DURATION_SECONDS, SHORTS_MIN_DURATION_SECONDS
from src.prompt_profiles import profile_prompt

MIN_LONGFORM_SECONDS = 420
MAX_LONGFORM_SECONDS = 1200

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
    'NÃO use posição fixa ou horário fixo, nem suponha que a propaganda esteja sempre '
    'no começo: cada vídeo pode ter publicidade em pontos e durações diferentes. No formato curto, '
    f'escolha uma janela completa de {SHORTS_MIN_DURATION_SECONDS:.0f} a '
    f'{SHORTS_MAX_DURATION_SECONDS:.0f} segundos; a posição deve ser encontrada semanticamente. Uma menção editorial '
    'a uma marca não é publicidade se não houver promoção, venda ou chamada comercial. Nenhum momento '
    'pode sobrepor publicidade, nem por poucos segundos. '
    'Para o ASSUNTO COMPLETO, encontre um único raciocínio com começo, meio e fim: introdução/contexto, '
    'desenvolvimento e conclusão. Infira os limites naturais deste assunto: comece quando a ideia é '
    'apresentada, incluindo a pergunta ou o setup necessário, e termine somente depois da resposta, '
    'desfecho ou conclusão, em uma pausa clara ou troca de assunto. NUNCA corte no meio de uma palavra, '
    'frase, fala, resposta, pergunta, explicação, história, piada ou raciocínio, nem em conjunções ou '
    'preposições ("mas", "porque", "então", "apesar de"). Para Shorts, procure um assunto completo '
    f'que caiba em uma janela de {SHORTS_MIN_DURATION_SECONDS:.0f} a '
    f'{SHORTS_MAX_DURATION_SECONDS:.0f} segundos; não force uma janela que corte o assunto. Se não '
    'houver segmento editorial completo e seguro, retorne {"moments": []}. Se aparecer o marcador '
    '[... trecho intermediário omitido ...], trate a lacuna como desconhecida; não atravesse essa lacuna '
    'nem crie um momento que a atravesse. '
    'IMPORTANTE: timestamps delimitam blocos da transcrição, NÃO necessariamente frases completas. '
    'Antes de definir end_time, leia a linha escolhida e as linhas seguintes. Se o texto terminar em '
    'vírgula, dois-pontos, reticências, travessão, conjunção, preposição, palavra que pede complemento '
    'ou continuar em minúscula na linha seguinte, avance end_time até fechar a oração, a resposta ou '
    'o raciocínio e alcançar pontuação final, pausa clara ou troca de assunto. Exemplo de corte proibido: '
    '"É diferente de você fazer," está incompleto; continue até incluir "faça um algoritmo, faça um '
    'pequeno trecho." Nunca pare só porque chegou ao fim de uma linha, atingiu a duração preferida ou '
    'encontrou um score alto. '
)

DUPLICATE_AVOIDANCE_RULE = (
    'REGRA OBRIGATÓRIA — ANTI-REPETIÇÃO: o usuário pode fornecer um HISTÓRICO DE TRECHOS JÁ '
    'UTILIZADOS NESTE VÍDEO, com intervalos em segundos e o status de cada registro. Trate todos '
    'esses intervalos como bloqueados: nunca escolha um momento que reutilize material falado ou '
    'se sobreponha a qualquer um deles por mais de 0.5 segundo. Escolha outro assunto ou outra parte ainda não '
    'utilizada da transcrição. Tema parecido não é, sozinho, repetição: só descarte quando o trecho '
    'novo reutilizar material falado do intervalo bloqueado. Se todos os candidatos bons estiverem '
    'bloqueados, retorne apenas os candidatos restantes ou {"moments": []}. '
)

SELECTION_VALIDATION_RULES = (
    'VALIDAÇÃO FINAL OBRIGATÓRIA — para cada candidato, releia a transcrição desde o início até '
    'end_time e também a continuação imediata. Confirme que o início não entra no meio de uma fala e '
    'que as últimas palavras formam uma frase, resposta ou ideia completa. Se end_time cair no fim de '
    'um bloco cuja oração continua, mova-o para depois da continuação; se não for possível confirmar '
    'o fechamento sem atravessar uma lacuna ou publicidade, descarte o candidato. '
)

SHORTFORM_CONTRACT_RULE = (
    f'CONTRATO TÉCNICO DO FORMATO CURTO — cada momento retornado deve durar de '
    f'{SHORTS_MIN_DURATION_SECONDS:.0f} a {SHORTS_MAX_DURATION_SECONDS:.0f} segundos: '
    'end_time - start_time deve ficar nesse intervalo. Prefira a menor janela que preserve o assunto '
    'completo. '
)

SYSTEM_PROMPT = (
    'Você é um especialista em identificar momentos virais de vídeos de futebol e podcasts esportivos. '
    'Analise a transcrição fornecida e identifique os melhores segmentos para criar clips CURTOS, '
    f'com duração entre {SHORTS_MIN_DURATION_SECONDS:.0f} e {SHORTS_MAX_DURATION_SECONDS:.0f} segundos. '
    f'Se o vídeo tiver menos de {SHORTS_MIN_DURATION_SECONDS:.0f} segundos, '
    'selecione o vídeo completo e marque-o para descarte na validação técnica. '
    + CONTENT_SELECTION_RULES
    + 'Para futebol: priorize análise tática, debate acalorado, revelação de bastidores e o COMENTÁRIO sobre um gol. '
    'Para podcasts: priorize discussão intensa, revelação importante, momento de conflito ou humor. '
    + FACT_CHECK_INSTRUCTION
    + DUPLICATE_AVOIDANCE_RULE
    + SELECTION_VALIDATION_RULES
    + 'Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente '
    '(10 = viral garantido, 1 = sem valor). '
    'IMPORTANTE: start_time e end_time DEVEM ser NÚMEROS inteiros em segundos (ex: 120, 350), NUNCA use formato com dois pontos como 21:21 ou strings. '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)

# Modo 'longo' (Processar Vídeo > formato=longo): 1 segmento contínuo de 7-20min
# em vez de vários momentos curtos. Prompt separado porque misturar duração longa
# com o pedido de vários momentos curtos reduz a aderência do modelo.
LONG_SYSTEM_PROMPT = (
    'Você é um especialista em identificar o melhor segmento de ANÁLISE ou ENTREVISTA longa '
    'de um vídeo de futebol/esportes para virar um vídeo único no YouTube (não um short). '
    'Analise a transcrição e identifique O MELHOR segmento CONTÍNUO — não fragmente em vários '
    f'pedaços — com duração entre {MIN_LONGFORM_SECONDS} e {MAX_LONGFORM_SECONDS} segundos. '
    'Priorize um raciocínio completo: uma análise tática do início ao fim, uma resposta longa e '
    'coesa de um entrevistado, ou um debate que se desenvolve com começo, meio e fim. Se o '
    'raciocínio natural não couber nessa duração, escolha outro segmento completo; não corte '
    'uma ideia só para atingir o teto. Não escolha um '
    'trecho curto — o segmento PRECISA ter pelo menos 420 segundos de duração '
    '(end_time - start_time >= 420). '
    + CONTENT_SELECTION_RULES
    + FACT_CHECK_INSTRUCTION
    + DUPLICATE_AVOIDANCE_RULE
    + SELECTION_VALIDATION_RULES
    + 'Retorne exatamente 1 momento, com score de 1 a 10 '
    '(10 = análise excelente pra virar vídeo, 1 = sem valor). '
    'IMPORTANTE: start_time e end_time DEVEM ser NÚMEROS inteiros em segundos (ex: 120, 350), NUNCA use formato com dois pontos como 21:21 ou strings. '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)

HACKER_LIBERTARIO_PROMPT = (
    'Você é um especialista em identificar momentos virais, insights profundos e explicações técnicas de alto impacto para o canal Hacker Libertário: '
    'Inteligência Artificial (IA), Open Source, Linux, Programação, Segurança, Criptografia, Privacidade, Soberania Digital e Cultura Hacker Libertária. '
    'Analise a transcrição fornecida e identifique os melhores segmentos para criar clips CURTOS, '
    f'com duração entre {SHORTS_MIN_DURATION_SECONDS:.0f} e {SHORTS_MAX_DURATION_SECONDS:.0f} segundos. '
    f'Se o vídeo tiver menos de {SHORTS_MIN_DURATION_SECONDS:.0f} segundos, '
    'selecione o vídeo completo e marque-o para descarte na validação técnica. '
    + CONTENT_SELECTION_RULES
    + 'DIRETRIZES LIBERTÁRIAS E EDITORIAIS INEGOCIÁVEIS: '
    '1. O ESTADO NUNCA DEVE SER DEFENDIDO: rejeite qualquer trecho que defenda, elogie, justifique ou legitime o Estado, impostos, regulação estatal, censura ou coerção governamental. Trechos sobre regulação ou vigilância só são válidos se forem de denúncia crítica e apresentarem alternativas de defesa individual por meio de tecnologia e criptografia. '
    '2. ZERO MENÇÃO A POLÍTICOS E FUNCIONÁRIOS PÚBLICOS: nenhum político (de qualquer partido) ou funcionário público/agente estatal deve ser sequer mencionado pelo nome ou colocado em evidência. Se houver politicagem ou debate partidário, descarte imediatamente. O foco é 100% nas ideias, ferramentas, tecnologia, privacidade e liberdade individual. '
    '3. GANCHO VIRAL IMEDIATO (0 A 3s): o corte deve começar no auge da afirmação de impacto ou pergunta provocativa; nunca comece com saudações, enrolação ou pausas. '
    'Priorize: explicações técnicas brilhantes, reflexões sobre soberania e privacidade digital, analogias marcantes sobre computação/IA e quebra de mitos. '
    + FACT_CHECK_INSTRUCTION
    + DUPLICATE_AVOIDANCE_RULE
    + SELECTION_VALIDATION_RULES
    + 'Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente '
    '(10 = viral garantido, 1 = sem valor). '
    'IMPORTANTE: start_time e end_time DEVEM ser NÚMEROS inteiros em segundos (ex: 120, 350), NUNCA use formato com dois pontos como 21:21 ou strings. '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)

HACKER_LIBERTARIO_LONG_PROMPT = (
    'Você é um especialista em identificar o melhor segmento de ANÁLISE técnica ou ENTREVISTA '
    'para o canal Hacker Libertário sobre Tecnologia, Inteligência Artificial, Linux, Open Source, Cibersegurança ou Filosofia Hacker '
    'para virar um vídeo único no YouTube (não um short). '
    'Analise a transcrição e identifique O MELHOR segmento CONTÍNUO — não fragmente em vários '
    f'pedaços — com duração entre {MIN_LONGFORM_SECONDS} e {MAX_LONGFORM_SECONDS} segundos. '
    'Priorize um raciocínio completo: uma explicação aprofundada de um conceito de IA/sistemas, '
    'uma reflexão densa sobre soberania tecnológica, ou um debate técnico do início ao fim. '
    + CONTENT_SELECTION_RULES
    + 'DIRETRIZES LIBERTÁRIAS E EDITORIAIS INEGOCIÁVEIS: '
    '1. O Estado nunca deve ser defendido nem legitimado em nenhuma regulação ou intervenção. '
    '2. Nenhum político ou funcionário público deve ser mencionado pelo nome ou colocado em debate. O canal trata de tecnologia, ideias e liberdade individual, nunca de politicagem. '
    + FACT_CHECK_INSTRUCTION
    + DUPLICATE_AVOIDANCE_RULE
    + SELECTION_VALIDATION_RULES
    + 'Retorne exatamente 1 momento, com score de 1 a 10 '
    '(10 = análise excelente pra virar vídeo, 1 = sem valor). '
    'IMPORTANTE: start_time e end_time DEVEM ser NÚMEROS inteiros em segundos (ex: 120, 350), NUNCA use formato com dois pontos como 21:21 ou strings. '
    'Responda APENAS com JSON válido, sem texto adicional:\n'
    '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
)


def _build_profile_selection_prompt(instruction: str, is_longo: bool) -> str:
    output_instruction = (
        'Retorne exatamente 1 momento, com score de 1 a 10 '
        '(10 = análise excelente pra virar vídeo, 1 = sem valor). '
        if is_longo
        else 'Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente '
        '(10 = viral garantido, 1 = sem valor). '
    )
    return (
        f'{instruction}\n'
        + CONTENT_SELECTION_RULES
        + (SHORTFORM_CONTRACT_RULE if not is_longo else '')
        + FACT_CHECK_INSTRUCTION
        + DUPLICATE_AVOIDANCE_RULE
        + SELECTION_VALIDATION_RULES
        + output_instruction
        + 'IMPORTANTE: start_time e end_time DEVEM ser NÚMEROS inteiros em segundos (ex: 120, 350), NUNCA use formato com dois pontos como 21:21 ou strings. '
        + 'Responda APENAS com JSON válido, sem texto adicional:\n'
        '{"moments": [{"start_time": <number>, "end_time": <number>, "score": <number>, "reason": "<string>", "fake_news": "<positivo|negativo|inconclusivo>"}]}'
    )


POLITICA_SELECTION_INSTRUCTION = (
    'Você é um especialista de elite em identificar os momentos de maior impacto, confrontos, quebras de narrativa e debates em vídeos e podcasts de POLÍTICA '
    '(focado na fórmula de cortes virais de alta retenção de canais de política e debates eleitorais/sabatinas). '
    'CRITÉRIOS DE CORTE VIRAL DE POLÍTICA: '
    '1. GANCHO FORTE (0 a 5 segundos): O segmento deve começar exatamente no início de uma pergunta provocativa, uma declaração polêmica ou o início de uma refutação contundente. '
    '2. CONFLITO & REFUTAÇÃO ("Jantada"): Priorize momentos onde uma narrativa é desconstruída com fatos/lógica, contradições são expostas ou há embate direto com alta carga emocional. '
    '3. RACIOCÍNIO FECHADO: Começo, meio e desfecho claro do argumento. Termine logo após a conclusão impactante ou momento de choque, sem sobras.'
)

POLITICA_SYSTEM_PROMPT = _build_profile_selection_prompt(POLITICA_SELECTION_INSTRUCTION, False)

POLITICA_LONG_SELECTION_INSTRUCTION = (
    'Você é um especialista em identificar o melhor bloco completo de sabatina, debate ou análise política '
    f'para virar um vídeo longo monetizável no YouTube ({MIN_LONGFORM_SECONDS // 60} a {MAX_LONGFORM_SECONDS // 60} minutos). '
    f'Analise a transcrição e identifique O MELHOR segmento CONTÍNUO com duração entre {MIN_LONGFORM_SECONDS} e {MAX_LONGFORM_SECONDS} segundos. '
    'Priorize um bloco temático fechado e aprofundado: uma discussão completa sobre um tema polêmico, '
    'uma entrevista reveladora ou um confronto de ideias do início ao desfecho do argumento.'
)

POLITICA_LONG_SYSTEM_PROMPT = _build_profile_selection_prompt(
    POLITICA_LONG_SELECTION_INSTRUCTION, True
)


GENERIC_SELECTION_INSTRUCTION = (
    'Você é um especialista em identificar momentos editoriais de alto potencial no nicho configurado. '
    'Analise a transcrição fornecida e escolha apenas segmentos completos, relevantes e seguros para o '
    'público desse canal. Não importe critérios, vocabulário ou fatos de outro nicho.'
)

GENERIC_SYSTEM_PROMPT = _build_profile_selection_prompt(GENERIC_SELECTION_INSTRUCTION, False)
GENERIC_LONG_SYSTEM_PROMPT = _build_profile_selection_prompt(GENERIC_SELECTION_INSTRUCTION, True)


def get_system_prompt(
    fmt: str = 'curto',
    niche: str | None = None,
    prompt_profile: Mapping[str, object] | None = None,
) -> str:
    is_longo = fmt == 'longo'
    profile_field = 'selection_long_prompt' if is_longo else 'selection_short_prompt'
    profile_instruction = profile_prompt(prompt_profile, profile_field)
    if profile_instruction:
        return _build_profile_selection_prompt(profile_instruction, is_longo)

    if niche in ('hacker-libertario', 'tecnologia', 'tech', 'linux', 'ia', 'opensource'):
        return HACKER_LIBERTARIO_LONG_PROMPT if is_longo else HACKER_LIBERTARIO_PROMPT
    if niche in ('politica', 'cortes-da-politica', 'debates', 'eleicoes'):
        return POLITICA_LONG_SYSTEM_PROMPT if is_longo else POLITICA_SYSTEM_PROMPT
    if not niche or niche not in ('futebol', 'esportes', 'podcast'):
        generic_prompt = GENERIC_LONG_SYSTEM_PROMPT if is_longo else GENERIC_SYSTEM_PROMPT
        return f'{generic_prompt}\nNicho configurado: {niche}.' if niche else generic_prompt
    return LONG_SYSTEM_PROMPT if is_longo else SYSTEM_PROMPT


MIN_SHORTFORM_SECONDS = int(SHORTS_MIN_DURATION_SECONDS)
MIN_SHORTFORM_CANDIDATE_SECONDS = 15.0
MAX_SHORTFORM_SECONDS = int(SHORTS_MAX_DURATION_SECONDS)

# Pequena tolerância para a borda de dois intervalos vizinhos. O filtro do
# banco bloqueia qualquer repetição material, mas não considera 0,5 s de ruído
# de arredondamento como sobreposição.
DUPLICATE_OVERLAP_TOLERANCE_SECONDS = 0.5

# Whisper/Groq costuma devolver timestamps com arredondamento. Se o modelo
# terminar até este intervalo antes do fim de uma fala, completar o segmento
# evita que o FFmpeg corte a última palavra.
TRANSCRIPT_BOUNDARY_TOLERANCE_SECONDS = 3.0
TRANSCRIPT_BOUNDARY_OPENING_SECONDS = 2.5
MAX_BOUNDARY_COMPLETION_SECONDS = 30.0
MAX_BOUNDARY_COMPLETION_GAP_SECONDS = 4.0
# ASR providers sometimes emit very long blocks. Snapping the end of a
# 2-minute block to its end would inflate a short clip and may swallow the
# next topic; only short blocks are safe to treat as one atomic spoken phrase.
MAX_ATOMIC_TRANSCRIPT_SEGMENT_SECONDS = 30.0

_INCOMPLETE_TRAILING_WORDS = frozenset(
    [
        'a',
        'ao',
        'aos',
        'as',
        'à',
        'às',
        'e',
        'ou',
        'mas',
        'porque',
        'que',
        'se',
        'quando',
        'como',
        'para',
        'pra',
        'pro',
        'de',
        'do',
        'da',
        'dos',
        'das',
        'em',
        'no',
        'na',
        'nos',
        'nas',
        'por',
        'com',
        'sem',
        'sob',
        'sobre',
        'entre',
        'um',
        'uma',
        'uns',
        'umas',
        'o',
        'os',
        'já',
        'mais',
        'menos',
        'muito',
        'tão',
        'até',
        'vai',
        'vou',
        'foi',
        'é',
        'era',
        'ser',
        'ter',
        'tem',
        'há',
        'cada',
        'qual',
        'onde',
        'quem',
        'isso',
        'essa',
        'esse',
        'meu',
        'minha',
        'seu',
        'sua',
    ]
)

# O modelo precisa de alguma folga para não começar no meio da introdução do
# assunto nem terminar na primeira frase da conclusão. A expansão é limitada
# por pausas da transcrição e pelo teto abaixo para não engolir o tópico seguinte.
LONGFORM_CONTEXT_BEFORE_SECONDS = 12.0
LONGFORM_CONTEXT_AFTER_SECONDS = 24.0
LONGFORM_MAX_CLOSING_EXTENSION_SECONDS = 180.0
LONGFORM_NATURAL_PAUSE_SECONDS = 2.5

# O modo curto retorna até três itens pequenos; manter a resposta compacta deixa
# espaço para a transcrição dentro do limite de TPM do Groq. O modo longo recebe
# Modelos maiores consumiam a cota diária rapidamente e, com teto curto, podiam
# gastar toda a resposta em raciocínio antes de emitir o JSON. O 20B com
# raciocínio baixo é suficiente para esta tarefa e deixa margem para o worker.
GROQ_CHAT_MODEL = (
    os.environ.get('GROQ_CHAT_MODEL') or os.environ.get('GROQ_MODEL') or 'openai/gpt-oss-20b'
)
GROQ_REASONING_EFFORT: Literal['low'] = 'low'
SELECTOR_MAX_OUTPUT_TOKENS = 2048
# A seleção longa precisa devolver apenas um momento em JSON. Manter a saída
# em 1k deixa margem para o limite total de tokens da API, mesmo com
# transcrições extensas e esforço de raciocínio baixo.
LONGFORM_SELECTOR_MAX_OUTPUT_TOKENS = 1024


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}', flush=True)


def _moment_interval(moment: dict) -> tuple[float, float] | None:
    """Retorna um intervalo válido de momento, ignorando dados incompletos."""
    try:
        start_time = float(moment['start_time'])
        end_time = float(moment['end_time'])
    except (KeyError, TypeError, ValueError):
        return None

    if end_time <= start_time:
        return None
    return start_time, end_time


def _format_used_moments_context(used_moments: list[dict] | None) -> list[str]:
    """Formata o histórico persistido para ser enviado junto da transcrição."""
    lines = []
    for moment in used_moments or []:
        interval = _moment_interval(moment)
        if interval is None:
            continue
        start_time, end_time = interval
        status = str(moment.get('status') or 'registrado')
        lines.append(f'- [{start_time:.2f}s-{end_time:.2f}s] status={status}')
    return lines


def _append_used_moments_context(transcript_text: str, used_moments: list[dict] | None) -> str:
    """Anexa à entrada da IA os intervalos do vídeo que não podem ser repetidos."""
    history_lines = _format_used_moments_context(used_moments)
    if not history_lines:
        return transcript_text

    return (
        transcript_text
        + '\n\n--- HISTÓRICO DE TRECHOS JÁ UTILIZADOS NESTE VÍDEO ---\n'
        + 'Os intervalos abaixo estão bloqueados e não podem ser selecionados novamente:\n'
        + '\n'.join(history_lines)
        + '\n--- FIM DO HISTÓRICO ---'
    )


def _intervals_overlap(first: tuple[float, float], second: tuple[float, float]) -> bool:
    """Diz se dois intervalos compartilham material além do ruído de borda."""
    overlap = min(first[1], second[1]) - max(first[0], second[0])
    return overlap > DUPLICATE_OVERLAP_TOLERANCE_SECONDS


def _remove_repeated_moments(moments: list[dict], used_moments: list[dict] | None) -> list[dict]:
    """Remove momentos que reutilizam intervalo já registrado para o vídeo."""
    used_intervals = [
        interval
        for moment in used_moments or []
        if (interval := _moment_interval(moment)) is not None
    ]
    if not used_intervals:
        return moments

    filtered = []
    for moment in moments:
        interval = _moment_interval(moment)
        if interval and any(_intervals_overlap(interval, used) for used in used_intervals):
            _log(
                f'[SELECTOR] Momento descartado por repetição: {interval[0]:.2f}-{interval[1]:.2f}s'
            )
            continue
        filtered.append(moment)
    return filtered


def _to_seconds(val) -> float:
    """Converte valores numéricos ou strings de tempo (ex: '21:21', '01:15:30', 120) para float em segundos."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace('s', '').replace('S', '')
        if ':' in val:
            try:
                parts = [float(p) for p in val.split(':')]
                if len(parts) == 2:
                    return parts[0] * 60 + parts[1]
                elif len(parts) == 3:
                    return parts[0] * 3600 + parts[1] * 60 + parts[2]
            except Exception:
                return 0.0
        try:
            return float(val)
        except ValueError:
            return 0.0
    return 0.0


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


def _clean_boundary_text(text: str | None) -> str:
    """Normaliza texto de uma legenda para avaliar se a fala terminou."""
    normalized = ' '.join(str(text or '').split())
    normalized = re.sub(r'^(?:>>\s*)+', '', normalized).strip()
    return re.sub(r'[\s"\'»”’\)\]}]+$', '', normalized).rstrip()


def _has_terminal_punctuation(text: str | None) -> bool:
    """Diz se o texto termina com pontuação que pode fechar uma frase."""
    return bool(re.search(r'[.!?]$', _clean_boundary_text(text)))


def _has_explicit_continuation(text: str | None) -> bool:
    """Detecta vírgula/conector no fim que exige continuação da fala."""
    normalized = _clean_boundary_text(text)
    if not normalized:
        return False
    if normalized.endswith(('...', '…', ',', ';', ':', '—', '–', '-')):
        return True

    words = re.findall(r'[^\W\d_]+', normalized.casefold(), flags=re.UNICODE)
    return bool(words and words[-1] in _INCOMPLETE_TRAILING_WORDS)


def _starts_like_continuation(text: str | None) -> bool:
    """Diz se a próxima legenda parece continuar a oração anterior."""
    normalized = _clean_boundary_text(text)
    normalized = normalized.lstrip('([{"“\'')
    match = re.match(r'[^\W\d_]+', normalized, flags=re.UNICODE)
    if not match:
        return False

    word = match.group(0)
    continuation_words = {
        'a',
        'ao',
        'aos',
        'as',
        'à',
        'às',
        'e',
        'ou',
        'mas',
        'porque',
        'que',
        'se',
        'quando',
        'como',
        'para',
        'pra',
        'pro',
        'de',
        'do',
        'da',
        'em',
        'no',
        'na',
        'por',
        'com',
        'sem',
        'então',
        'apesar',
        'embora',
    }
    return word[0].islower() or word.casefold() in continuation_words


def _needs_boundary_completion(text: str | None, next_text: str | None) -> bool:
    """Diz se a fala atual ainda depende do próximo bloco da transcrição."""
    if _has_explicit_continuation(text):
        return True
    if _has_terminal_punctuation(text):
        return False
    return _starts_like_continuation(next_text)


def _extend_boundary_to_complete_thought(
    segments: list[tuple[float, float, str]], boundary_index: int, current_end: float
) -> float:
    """Avança um limite quando o bloco escolhido termina numa oração aberta.

    A transcrição do YouTube/Whisper quebra a fala em blocos temporais que não
    são necessariamente frases. A extensão é limitada para não atravessar uma
    pausa longa ou engolir o assunto seguinte.
    """
    if boundary_index < 0 or boundary_index >= len(segments):
        return current_end

    text = segments[boundary_index][2]
    original_end = current_end
    for next_index in range(boundary_index + 1, len(segments)):
        next_start, next_end, next_text = segments[next_index]
        if not _needs_boundary_completion(text, next_text):
            break
        if next_start - current_end > MAX_BOUNDARY_COMPLETION_GAP_SECONDS:
            break
        if next_start - original_end > MAX_BOUNDARY_COMPLETION_SECONDS:
            break

        text = f'{text} {next_text}'.strip()
        current_end = max(current_end, next_end)
        following_text = segments[next_index + 1][2] if next_index + 1 < len(segments) else None
        if not _needs_boundary_completion(text, following_text):
            break

    return current_end


def complete_moment_boundaries(
    moments: list[dict], transcript_segments: list[dict] | None
) -> list[dict]:
    """Completa limites das falas, sem parar numa oração aberta.

    Proteções implementadas:
    - start_time: Se cair logo no início de um segmento (<= 3.0s), recua para o início exato da fala.
    - end_time:
      * Se cair muito no início de um novo segmento (ex: <= 2.5s), recua (snap back) para o fim do
        segmento anterior, evitando pegar apenas o começo de uma frase inacabada ("Apesar de...").
      * Se cair perto do fim de um segmento, avança até o fim daquele segmento.
      * Se o bloco terminar com uma oração aberta, também inclui os blocos seguintes até a ideia fechar.
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
            segments.append((segment_start, segment_end, str(segment.get('text') or '')))

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

        # Ajuste de início. Só recuamos quando a IA caiu perto do início do
        # bloco; um recuo incondicional poderia incluir uma introdução inteira
        # que o modelo deliberadamente deixou fora do corte.
        for segment_start, segment_end, _ in segments:
            if segment_start <= start_time < segment_end:
                if start_time - segment_start <= tolerance:
                    new_start = segment_start
                break

        # Ajuste de fim
        end_segment_index = None
        nearby_endings = [
            (abs(end_time - segment_end), seg_idx)
            for seg_idx, (_, segment_end, _) in enumerate(segments)
            if abs(end_time - segment_end) <= tolerance
        ]
        if nearby_endings:
            # Um fim exato deve ganhar de um bloco anterior que por acaso acaba
            # até três segundos antes (caso real: 536.519 vs. 534.120).
            _, end_segment_index = min(nearby_endings, key=lambda item: (item[0], -item[1]))
            new_end = segments[end_segment_index][1]
        else:
            for seg_idx, (segment_start, segment_end, _) in enumerate(segments):
                if segment_start < end_time < segment_end:
                    # Se o timestamp pegaria apenas os primeiros segundos de um novo segmento (<= 2.5s)
                    if (
                        end_time - segment_start
                    ) <= TRANSCRIPT_BOUNDARY_OPENING_SECONDS and seg_idx > 0:
                        prev_end = segments[seg_idx - 1][1]
                        new_end = prev_end
                        end_segment_index = seg_idx - 1
                    elif segment_end - segment_start <= MAX_ATOMIC_TRANSCRIPT_SEGMENT_SECONDS:
                        # Quando o modelo encerra no meio de um bloco, o
                        # limite seguro é o fim do bloco. Assim o clip nunca
                        # corta a última frase apenas porque a IA arredondou
                        # o timestamp.
                        new_end = segment_end
                        end_segment_index = seg_idx
                    break

        if end_segment_index is not None:
            new_end = _extend_boundary_to_complete_thought(segments, end_segment_index, new_end)

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


MAX_REASON_CHARS = 300


def _clean_reason(raw) -> str:
    """Colapsa espaços e corta a justificativa do momento em MAX_REASON_CHARS.

    Modelo que raciocina em voz alta despeja a cadeia de pensamento inteira no campo `reason`
    ("Vou selecionar o trecho de 0s a 454s? Não, o início é fraco. Vou..."). Visto em produção
    com o Groq em 15/09/2026. A coluna é TEXT, então nada estoura — o estrago é metadado
    ilegível no painel e no log, que é onde a justificativa é lida.
    """
    if raw is None:
        return ''
    texto = ' '.join(str(raw).split())
    if len(texto) > MAX_REASON_CHARS:
        return texto[:MAX_REASON_CHARS].rstrip() + '…'
    return texto


def _parse_moments(raw_text: str) -> list[dict]:
    """Parse JSON text → lista de dicts de momentos com resiliência a markdown, formatação e timestamps."""
    text = (raw_text or '').strip()
    if not text:
        return []

    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Tenta extrair bloco ```json ... ```
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        if data is None:
            # Tenta encontrar primeiro { até o último }
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

    if not isinstance(data, dict):
        _log(f'[SELECTOR] Resposta da IA não pôde ser parseada como JSON válido: {text[:200]}')
        return []

    raw_moments = data.get('moments', [])
    if not isinstance(raw_moments, list):
        return []

    cleaned = []
    for m in raw_moments:
        if not isinstance(m, dict):
            continue
        try:
            start = _to_seconds(m.get('start_time', 0))
            end = _to_seconds(m.get('end_time', 0))
            if end <= start or start < 0:
                continue
            m_clean = dict(m)
            m_clean['start_time'] = start
            m_clean['end_time'] = end
            m_clean['reason'] = _clean_reason(m.get('reason'))
            cleaned.append(m_clean)
        except (TypeError, ValueError):
            continue

    moments = _normalize_scores(cleaned)
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


GROQ_MODEL = GROQ_CHAT_MODEL
GROQ_MAX_OUTPUT_TOKENS = int(os.environ.get('GROQ_MAX_OUTPUT_TOKENS', '1000'))


def _select_via_groq(
    transcript_text: str,
    system_prompt: str = SYSTEM_PROMPT,
    *,
    max_tokens: int | None = None,
) -> list[dict]:
    """Seleciona momentos via Groq (fallback sempre disponível)."""
    from groq import Groq
    from groq.types.chat import ChatCompletionMessageParam
    from groq.types.chat.completion_create_params import ResponseFormatResponseFormatJsonObject

    effective_max_tokens = min(max_tokens or GROQ_MAX_OUTPUT_TOKENS, GROQ_MAX_OUTPUT_TOKENS)

    client = Groq()
    _log(f'[SELECTOR] Usando Groq LLM ({GROQ_MODEL})')
    messages: list[ChatCompletionMessageParam] = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': transcript_text},
    ]
    response_format: ResponseFormatResponseFormatJsonObject = {'type': 'json_object'}
    kwargs: dict[str, Any] = {
        'model': GROQ_MODEL,
        'messages': messages,
        'response_format': response_format,
        'temperature': 0.2,
        'max_tokens': effective_max_tokens,
    }
    if 'gpt-oss' in GROQ_MODEL or 'o1' in GROQ_MODEL:
        kwargs['reasoning_effort'] = GROQ_REASONING_EFFORT
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as error:
        error_text = str(error).casefold()
        if 'json_validate_failed' not in error_text and 'failed to validate json' not in error_text:
            raise
        _log(
            '[SELECTOR] Groq rejeitou a saída JSON estruturada — '
            'repetindo uma vez sem response_format'
        )
        fallback_kwargs = dict(kwargs)
        fallback_kwargs.pop('response_format', None)
        response = client.chat.completions.create(**fallback_kwargs)
    content = response.choices[0].message.content or ''
    moments = _parse_moments(content)
    if not moments:
        _log('[SELECTOR] Groq não retornou momento válido para esta janela')
    return moments


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
    """Garante duração mínima de MIN_LONGFORM_SECONDS e máxima de MAX_LONGFORM_SECONDS para o modo 'longo'.

    O modelo (mesmo instruído) às vezes devolve segmentos curtos ou excessivamente longos.
    Ajustamos para garantir conformidade estrita com MIN_LONGFORM_SECONDS e MAX_LONGFORM_SECONDS.
    """
    adjusted: list[dict] = []
    for m in moments:
        m_copy = dict(m)
        start = float(m_copy.get('start_time', 0))
        end = float(m_copy.get('end_time', 0))
        duration = end - start

        # Limitar teto máximo primeiro
        if duration > MAX_LONGFORM_SECONDS:
            _log(
                f'[SELECTOR] Momento longo ({duration:.1f}s) limitado para o máximo ({MAX_LONGFORM_SECONDS}s)'
            )
            end = start + MAX_LONGFORM_SECONDS
            duration = MAX_LONGFORM_SECONDS
            m_copy['end_time'] = end

        if duration >= MIN_LONGFORM_SECONDS:
            adjusted.append(m_copy)
            continue

        target = (
            min(MIN_LONGFORM_SECONDS, transcript_duration)
            if transcript_duration
            else MIN_LONGFORM_SECONDS
        )
        missing = target - duration
        new_start = max(0, start - missing / 2)
        new_end = new_start + target
        if transcript_duration and new_end > transcript_duration:
            new_end = transcript_duration
            new_start = max(0, new_end - target)

        m_copy['start_time'] = new_start
        m_copy['end_time'] = min(new_end, new_start + MAX_LONGFORM_SECONDS)
        adjusted.append(m_copy)
    return adjusted


def _filter_shortform_duration(
    moments: list[dict], transcript_duration: float | None = None
) -> list[dict]:
    """Garante o mínimo de 30s e conserva durações até o máximo configurado."""
    valid: list[dict] = []
    target_duration = SHORTS_MIN_DURATION_SECONDS

    if transcript_duration is not None and transcript_duration < target_duration:
        _log(
            f'[SELECTOR] Vídeo descartado: transcrição tem {transcript_duration:.1f}s, '
            'menos que os 30s mínimos para um Short'
        )
        return valid

    for m in moments:
        start_time = float(m.get('start_time', 0))
        end_time = float(m.get('end_time', 0))
        duration = end_time - start_time
        if duration < target_duration:
            if duration < MIN_SHORTFORM_CANDIDATE_SECONDS:
                _log(
                    f'[SELECTOR] Momento descartado: duração {duration:.1f}s menor que os '
                    f'{MIN_SHORTFORM_CANDIDATE_SECONDS:.0f}s mínimos'
                )
                continue

            # O alinhamento com a última frase pode encurtar o intervalo por
            # uma fração de segundo. Completa a janela pelo começo, ou pelo
            # fim quando o candidato já começa em zero, sem ultrapassar a
            # duração conhecida da transcrição.
            missing = target_duration - duration
            normalized_start = max(0.0, start_time - missing)
            normalized_end = normalized_start + target_duration
            if transcript_duration and normalized_end > transcript_duration:
                normalized_end = transcript_duration
                normalized_start = max(0.0, normalized_end - target_duration)
            if round(normalized_end - normalized_start, 2) < target_duration:
                _log(
                    f'[SELECTOR] Momento descartado: não há margem para completar '
                    f'{target_duration:.0f}s dentro da transcrição'
                )
                continue

            normalized = dict(m)
            normalized['start_time'] = round(normalized_start, 2)
            normalized['end_time'] = round(normalized_end, 2)
            valid.append(normalized)
            continue
        if duration > MAX_SHORTFORM_SECONDS:
            _log(
                f'[SELECTOR] Momento ajustado: duração {duration:.1f}s limitada para {MAX_SHORTFORM_SECONDS}s'
            )
            duration = MAX_SHORTFORM_SECONDS
        else:
            duration = max(duration, target_duration)
        if transcript_duration is not None:
            duration = min(duration, transcript_duration)
        if duration < target_duration:
            _log(
                f'[SELECTOR] Momento descartado: há apenas {duration:.1f}s disponíveis '
                'na transcrição'
            )
            continue
        normalized_start = max(0.0, start_time)
        if transcript_duration is not None:
            normalized_start = min(normalized_start, max(0.0, transcript_duration - duration))
        normalized = dict(m)
        normalized['start_time'] = round(normalized_start, 2)
        normalized['end_time'] = round(normalized_start + duration, 2)
        valid.append(normalized)
    return valid


def normalize_shortform_moment(
    moment: dict, transcript_duration: float | None = None
) -> dict | None:
    """Normaliza um intervalo legado para o contrato de Short, se possível."""
    normalized = _filter_shortform_duration([moment], transcript_duration)
    return normalized[0] if normalized else None


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


def _snap_to_sentence_boundaries(
    moments: list[dict], segments: list[dict], buffer_end: float = 1.0
) -> list[dict]:
    """Ajusta os timestamps dos momentos para respeitar os finais reais de frases do Whisper.

    Evita cortes no meio de uma oração ou pensamento incompleto.
    """
    if not segments or not moments:
        return moments

    snapped = []
    for m in moments:
        start_req = float(m['start_time'])
        end_req = float(m['end_time'])

        # Encontra o melhor início (apenas se houver fronteira próxima dentro de 3s)
        best_start = start_req
        for seg in segments:
            s_start = float(seg.get('start', 0))
            s_end = float(seg.get('end', 0))
            if s_start <= start_req <= s_end:
                if abs(start_req - s_start) <= 3.0:
                    best_start = s_start
                break

        # Encontra o melhor fim (apenas se houver fronteira próxima dentro de 3s)
        best_end = end_req
        for seg in segments:
            s_start = float(seg.get('start', 0))
            s_end = float(seg.get('end', 0))
            if s_start <= end_req <= s_end:
                if abs(s_end - end_req) <= 3.0:
                    best_end = s_end + buffer_end
                break

        snapped_m = dict(m)
        snapped_m['start_time'] = round(best_start, 2)
        snapped_m['end_time'] = round(best_end, 2)
        snapped.append(snapped_m)

    return snapped


def select_moments(
    transcript: dict,
    anthropic_client=None,
    fmt: str = 'curto',
    niche: str | None = 'futebol',
    used_moments: list[dict] | None = None,
    prompt_profile: Mapping[str, object] | None = None,
) -> list[dict]:
    """Analisa transcrição e retorna momentos selecionados via IA.

    Args:
        transcript: dict com {'video_id', 'text', 'segments'} — output de transcribe_video()
        anthropic_client: cliente Anthropic injetado para testes (None = modo produção)
        fmt: 'curto' (vários momentos de 30s-3min, padrão) ou 'longo' (1 segmento contínuo)
        niche: slug do nicho (ex: 'futebol', 'politica', 'hacker-libertario', 'podcast') para calibrar o prompt
        used_moments: intervalos já registrados para este vídeo. São enviados à IA como
            bloqueados e filtrados novamente antes do retorno.
        prompt_profile: perfil ativo do canal-fonte. Quando presente, suas instruções
            específicas têm precedência sobre os prompts legados por nicho.

    Returns:
        Lista de dicts com {'start_time', 'end_time', 'score', 'reason'}, sem overlap.
    """
    is_longo = fmt == 'longo'
    system_prompt = get_system_prompt(fmt=fmt, niche=niche, prompt_profile=prompt_profile)
    max_moments = 1 if is_longo else 3
    used_moments = used_moments or []
    segments = transcript.get('segments', [])

    lines = []
    transcript_duration = 0.0
    for seg in segments:
        start = float(seg['start'])
        end = float(seg['end'])
        if end > transcript_duration:
            transcript_duration = end
        lines.append(f'[{int(start)}s-{int(end)}s] {seg["text"]}')
    transcript_text = '\n'.join(lines)

    MAX_CHARS = 10000 if is_longo else 8000
    selector_max_tokens = (
        LONGFORM_SELECTOR_MAX_OUTPUT_TOKENS if is_longo else SELECTOR_MAX_OUTPUT_TOKENS
    )

    if len(transcript_text) > MAX_CHARS:
        if is_longo:
            visible_lines: list[str] = []
            visible_chars = 0
            for line in transcript_text.splitlines():
                line_size = len(line) + (1 if visible_lines else 0)
                if visible_lines and visible_chars + line_size > MAX_CHARS:
                    break
                visible_lines.append(line)
                visible_chars += line_size
            transcript_text = '\n'.join(visible_lines)
        else:
            transcript_text = transcript_text[:MAX_CHARS]
        _log(f'[SELECTOR] Transcrição truncada para {MAX_CHARS} chars (janela contínua)')

    if not transcript_text.strip():
        _log('[SELECTOR] Transcrição vazia — sem momentos')
        return []

    transcript_text = _append_used_moments_context(transcript_text, used_moments)

    def _finalize(moments: list[dict]) -> list[dict]:
        moments = _clamp_moment_bounds(moments, transcript_duration)
        moments = complete_moment_boundaries(moments, segments)
        moments = _snap_to_sentence_boundaries(moments, segments)
        if is_longo:
            moments = expand_longform_context(moments, segments)
        moments = _remove_repeated_moments(moments, used_moments)
        result = _remove_overlaps(moments, max_count=max_moments)
        if is_longo:
            result = _enforce_longform_duration(result, transcript_duration)
            result = _clamp_moment_bounds(result, transcript_duration)
            result = complete_moment_boundaries(result, segments)
            result = expand_longform_context(result, segments)
            result = _clamp_moment_bounds(result, transcript_duration)
            result = _enforce_longform_duration(result, transcript_duration)
            result = complete_moment_boundaries(result, segments)
            result = _remove_repeated_moments(result, used_moments)
        else:
            result = _filter_shortform_duration(result, transcript_duration)
            result = _remove_overlaps(result, max_count=max_moments)
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

    try:
        provider = os.environ.get('AI_PROVIDER', 'groq').strip().lower()
        if provider == 'anthropic':
            api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
            if not api_key:
                raise RuntimeError('AI_PROVIDER=anthropic exige ANTHROPIC_API_KEY configurada')
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            _log('[SELECTOR] Usando Anthropic por configuração explícita')
            moments = _select_via_anthropic_client(client, transcript_text, system_prompt)
        elif provider == 'groq':
            moments = _select_via_groq(
                transcript_text,
                system_prompt,
                max_tokens=selector_max_tokens,
            )
        else:
            raise ValueError(f'AI_PROVIDER inválido: {provider!r}; use groq ou anthropic')
        if not moments and is_longo and transcript_duration >= 420:
            _log('[SELECTOR] Fallback longo ativado: usando bloco principal contínuo do vídeo')
            start = 30.0 if transcript_duration > 600 else 10.0
            end = min(transcript_duration - 10.0, start + 780.0)
            if end - start >= 420:
                moments = [
                    {
                        'start_time': start,
                        'end_time': end,
                        'score': 8,
                        'reason': 'Recorte contínuo do tema principal do vídeo',
                    }
                ]
        return _finalize(moments)
    except Exception as e:
        _log(f'Erro ao selecionar momentos: {e}')
        return []


def _lookup_destination_channel_id(conn, source_video_id: int) -> int | None:
    """Resolve destination_channel_id via JOIN source_videos → source_channels → destination_channels."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT sc.target_niche, pp.id AS prompt_profile_id '
            'FROM source_videos sv '
            'JOIN source_channels sc ON sc.id = sv.channel_id '
            'LEFT JOIN prompt_profiles pp '
            'ON pp.id = sc.prompt_profile_id AND pp.active = TRUE '
            'WHERE sv.id = %s',
            (source_video_id,),
        )
        row = cur.fetchone()

    if not row or not row.get('target_niche'):
        return None

    target_niche = row['target_niche']
    prompt_profile_id = row.get('prompt_profile_id')

    with conn.cursor() as cur:
        if prompt_profile_id is not None:
            cur.execute(
                'SELECT id FROM destination_channels '
                'WHERE prompt_profile_id = %s AND active = TRUE '
                'AND EXISTS (SELECT 1 FROM prompt_profiles pp '
                'WHERE pp.id = destination_channels.prompt_profile_id AND pp.active = TRUE) '
                'ORDER BY id LIMIT 1',
                (prompt_profile_id,),
            )
        else:
            cur.execute(
                'SELECT id FROM destination_channels '
                'WHERE niche = %s AND active = TRUE '
                'AND (prompt_profile_id IS NULL OR EXISTS (SELECT 1 FROM prompt_profiles pp '
                'WHERE pp.id = destination_channels.prompt_profile_id AND pp.active = TRUE)) '
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
    # Consulta novamente imediatamente antes do INSERT: a seleção pode ter
    # demorado enquanto outro worker registrava um clip para o mesmo vídeo.
    used_moments = fetch_used_moments(conn, source_video_id)
    filtered = _remove_overlaps(_remove_repeated_moments(moments, used_moments))
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
