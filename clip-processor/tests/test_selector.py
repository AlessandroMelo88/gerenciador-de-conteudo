"""
test_selector.py — Testes unitários para selector.py (AI-02, AI-03).

Os cenários cobrem seleção por formato, validação da resposta e persistência.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src import selector as selector_module
from src.selector import (
    HACKER_LIBERTARIO_LONG_PROMPT,
    HACKER_LIBERTARIO_PROMPT,
    LONG_SYSTEM_PROMPT,
    LONGFORM_SELECTOR_MAX_OUTPUT_TOKENS,
    MAX_REASON_CHARS,
    SYSTEM_PROMPT,
    _clean_reason,
    _parse_moments,
    complete_moment_boundaries,
    expand_longform_context,
    get_system_prompt,
    insert_selected_moments,
    select_moments,
)

SAMPLE_TRANSCRIPT = {
    'video_id': 'dQw4w9WgXcQ',
    'text': 'Texto completo do vídeo',
    'segments': [
        {'start': 0.0, 'end': 60.0, 'text': 'Análise do gol de placa do Vini Jr'},
        {'start': 60.0, 'end': 120.0, 'text': 'Debate sobre o melhor jogador da temporada'},
        {'start': 120.0, 'end': 300.0, 'text': 'Tática do Ancelotti explicada'},
    ],
}

SAMPLE_MOMENTS = [
    {'start_time': 0.0, 'end_time': 60.0, 'score': 9, 'reason': 'Análise tática profunda'},
    {'start_time': 100.0, 'end_time': 160.0, 'score': 8, 'reason': 'Debate acalorado'},
    {'start_time': 200.0, 'end_time': 245.0, 'score': 7, 'reason': 'Revelação de bastidores'},
]


class TestCleanReason:
    """Justificativa do momento não pode carregar o raciocínio do modelo (visto em 15/09/2026)."""

    def test_colapsa_espacos_e_quebras(self):
        assert _clean_reason('Análise\n  tática   profunda\n') == 'Análise tática profunda'

    def test_ausente_vira_string_vazia(self):
        """insert_selected_moments lê moment['reason'] direto — não pode faltar a chave."""
        assert _clean_reason(None) == ''

    def test_corta_raciocinio_longo_do_modelo(self):
        raciocinio = (
            'Vou selecionar o trecho de 0s a 454s? Não, o início é fraco. '
            'Vou selecionar de 120s a 454s? Não atinge 420s. ' * 20
        )
        resultado = _clean_reason(raciocinio)

        assert len(resultado) == MAX_REASON_CHARS + 1  # +1 pela reticência
        assert resultado.endswith('…')

    def test_parse_moments_aplica_limpeza(self):
        """A limpeza tem que valer para os dois caminhos de IA, que passam por _parse_moments."""
        bruto = json.dumps(
            {
                'moments': [
                    {
                        'start_time': 0,
                        'end_time': 60,
                        'score': 9,
                        'reason': 'x' * (MAX_REASON_CHARS + 50),
                    }
                ]
            }
        )

        momentos = _parse_moments(bruto)

        assert len(momentos[0]['reason']) == MAX_REASON_CHARS + 1

    def test_parse_moments_preenche_reason_ausente(self):
        bruto = json.dumps({'moments': [{'start_time': 0, 'end_time': 60, 'score': 9}]})

        momentos = _parse_moments(bruto)

        assert momentos[0]['reason'] == ''


class TestSelectMoments:
    def test_groq_retries_without_structured_output_after_json_validation_error(self, monkeypatch):
        class FakeError(Exception):
            pass

        class FakeMessage:
            content = (
                '{"moments": [{"start_time": 0, "end_time": 30, "score": 9, "reason": "Insight"}]}'
            )

        class FakeResponse:
            def __init__(self):
                self.choices = [type('Choice', (), {'message': FakeMessage()})()]

        class FakeCompletions:
            def __init__(self):
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                if len(self.calls) == 1:
                    raise FakeError('code=json_validate_failed')
                return FakeResponse()

        completions = FakeCompletions()

        class FakeClient:
            chat = type('Chat', (), {'completions': completions})()

        class FakeGroq:
            def __new__(cls):
                return FakeClient()

        fake_groq_module = type('GroqModule', (), {'Groq': FakeGroq})
        fake_types_chat = type('ChatTypes', (), {'ChatCompletionMessageParam': dict})
        fake_types_params = type(
            'CompletionParams',
            (),
            {'ResponseFormatResponseFormatJsonObject': dict},
        )
        monkeypatch.setitem(__import__('sys').modules, 'groq', fake_groq_module)
        monkeypatch.setitem(__import__('sys').modules, 'groq.types', type('GroqTypes', (), {})())
        monkeypatch.setitem(__import__('sys').modules, 'groq.types.chat', fake_types_chat)
        monkeypatch.setitem(
            __import__('sys').modules,
            'groq.types.chat.completion_create_params',
            fake_types_params,
        )

        result = selector_module._select_via_groq('transcrição')

        assert result[0]['start_time'] == 0
        assert len(completions.calls) == 2
        assert completions.calls[0]['response_format'] == {'type': 'json_object'}
        assert 'response_format' not in completions.calls[1]

    def test_database_profile_takes_precedence_over_niche_fallback(self):
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'moments': [
                            {
                                'start_time': 0.0,
                                'end_time': 60.0,
                                'score': 9,
                                'reason': 'Insight técnico',
                            }
                        ]
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = mock_response

        select_moments(
            SAMPLE_TRANSCRIPT,
            anthropic_client=mock_anthropic,
            niche='futebol',
            prompt_profile={
                'slug': 'conteudo-inteligencia',
                'selection_short_prompt': 'PERFIL DE INTELIGÊNCIA: priorize tecnologia.',
            },
        )

        system_prompt = mock_anthropic.messages.create.call_args.kwargs['system']
        assert 'PERFIL DE INTELIGÊNCIA' in system_prompt
        assert 'vídeos de futebol brasileiro' not in system_prompt

    def test_long_selection_uses_long_prompt_field(self):
        system_prompt = get_system_prompt(
            fmt='longo',
            niche='futebol',
            prompt_profile={
                'selection_short_prompt': 'PROMPT CURTO',
                'selection_long_prompt': 'PROMPT LONGO DO PERFIL',
            },
        )

        assert 'PROMPT LONGO DO PERFIL' in system_prompt
        assert 'PROMPT CURTO' not in system_prompt

    def test_longform_groq_budget_stays_within_free_tier(self, monkeypatch):
        """O seletor longo não deve pedir uma resposta que estoure o TPM do Groq."""
        captured = {}

        def fake_groq(transcript_text, system_prompt, *, max_tokens):
            captured['max_tokens'] = max_tokens
            return [
                {
                    'start_time': 0.0,
                    'end_time': 420.0,
                    'score': 9,
                    'reason': 'Análise completa',
                }
            ]

        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        monkeypatch.setattr('src.selector._select_via_groq', fake_groq)

        select_moments(
            {
                'video_id': 'long001aaaa',
                'text': 'Texto longo',
                'segments': [{'start': 0.0, 'end': 600.0, 'text': 'Análise completa.'}],
            },
            fmt='longo',
        )

        assert captured['max_tokens'] == LONGFORM_SELECTOR_MAX_OUTPUT_TOKENS

    def test_all_selection_prompts_detect_ads_and_complete_topics(self):
        """Todos os formatos delegam os limites de anúncios e assuntos à IA por vídeo."""
        prompts = (
            SYSTEM_PROMPT,
            LONG_SYSTEM_PROMPT,
            HACKER_LIBERTARIO_PROMPT,
            HACKER_LIBERTARIO_LONG_PROMPT,
        )

        for prompt in prompts:
            normalized = prompt.casefold()
            assert 'propaganda' in normalized
            assert 'publicidade' in normalized
            assert 'timestamps' in normalized
            assert 'infira' in normalized
            assert 'posição fixa' in normalized
            assert '30 a 45 segundos' in normalized
            assert 'não atravesse essa lacuna' in normalized
            assert 'assunto completo' in normalized
            assert 'conclusão' in normalized
            assert 'nunca corte' in normalized
            assert 'não necessariamente frases completas' in normalized
            assert 'é diferente de você fazer' in normalized
            assert 'validação final obrigatória' in normalized
            assert '65s' not in normalized
            assert 'pesquise na internet' in normalized
            assert 'fake_news' in normalized
            assert 'positivo' in normalized and 'negativo' in normalized
            assert 'anti-repetição' in normalized
            assert 'histórico de trechos já utilizados' in normalized

    def test_returns_moments_list(self, sample_video_id):
        """AI-02: select_moments() retorna lista de dicts com start_time, end_time, score, reason."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': SAMPLE_MOMENTS}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic)

        assert isinstance(result, list)
        assert len(result) > 0
        first = result[0]
        assert 'start_time' in first
        assert 'end_time' in first
        assert 'score' in first
        assert 'reason' in first

    def test_fact_check_label_is_requested_and_preserved(self, sample_video_id):
        """Fatos recebem instrução de pesquisa e o selo é mantido no motivo do clip."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'moments': [
                            {
                                'start_time': 0.0,
                                'end_time': 60.0,
                                'score': 9,
                                'reason': 'Afirmação sobre o jogo',
                                'fake_news': 'positivo',
                            }
                        ]
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic)

        system_prompt = mock_anthropic.messages.create.call_args.kwargs['system']
        assert 'pesquise na internet' in system_prompt
        assert 'positivo' in system_prompt and 'negativo' in system_prompt
        assert result[0]['fake_news'] == 'positivo'
        assert result[0]['reason'].endswith('Fake news: positivo')

    def test_transcript_formatted_with_timestamps(self, sample_video_id):
        """AI-02: O texto enviado ao Haiku inclui timestamps no formato [Ns-Ns] por segmento."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': SAMPLE_MOMENTS}))]
        mock_anthropic.messages.create.return_value = mock_response

        select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic)

        # Verificar que o conteúdo enviado ao Haiku tem formato [Ns-Ns]
        call_args = mock_anthropic.messages.create.call_args
        (
            call_args[1]['messages']
            if 'messages' in call_args[1]
            else call_args[0][3]
            if len(call_args[0]) > 3
            else None
        )
        # Alternativa: verificar o kwarg 'messages'
        kwargs = call_args.kwargs if hasattr(call_args, 'kwargs') else call_args[1]
        user_content = kwargs['messages'][0]['content']
        assert '[0s-60s]' in user_content or '[0s-' in user_content

    def test_used_moments_are_sent_to_ai_and_filtered_from_result(self, sample_video_id):
        """A IA recebe o histórico e um intervalo já usado não volta no resultado."""
        mock_anthropic = MagicMock()
        response_moments = [
            {'start_time': 0.0, 'end_time': 60.0, 'score': 10, 'reason': 'Trecho já publicado'},
            {'start_time': 120.0, 'end_time': 180.0, 'score': 8, 'reason': 'Novo trecho'},
        ]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': response_moments}))]
        mock_anthropic.messages.create.return_value = mock_response

        used_moments = [
            {'start_time': 0.0, 'end_time': 60.0, 'status': 'published'},
        ]
        result = select_moments(
            SAMPLE_TRANSCRIPT,
            anthropic_client=mock_anthropic,
            used_moments=used_moments,
        )

        user_content = mock_anthropic.messages.create.call_args.kwargs['messages'][0]['content']
        assert 'HISTÓRICO DE TRECHOS JÁ UTILIZADOS NESTE VÍDEO' in user_content
        assert '[0.00s-60.00s] status=published' in user_content
        assert len(result) == 1
        assert result[0]['start_time'] == 120.0

    def test_shortform_under_30s_discarded(self, sample_video_id):
        """Momento com menos de 15 s é descartado: em 3-5 s não há assunto.

        Esticar 3 s até 30 s não cria assunto — só adiciona contexto aleatório em volta
        de uma interjeição. Abaixo do piso de esticamento, descarta.
        """
        mock_anthropic = MagicMock()
        short_moments = [
            {'start_time': 10.0, 'end_time': 13.0, 'score': 9, 'reason': 'Irrelevante de 3s'},
            {'start_time': 20.0, 'end_time': 25.0, 'score': 8, 'reason': 'Irrelevante de 5s'},
            {'start_time': 100.0, 'end_time': 140.0, 'score': 9, 'reason': 'Corte válido de 40s'},
        ]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': short_moments}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic, fmt='curto')

        assert len(result) == 1
        assert result[0]['start_time'] == 100.0
        assert result[0]['end_time'] == 140.0

    def test_shortform_is_clamped_to_maximum_duration(self):
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'moments': [
                            {
                                'start_time': 115.0,
                                'end_time': 165.0,
                                'score': 9,
                                'reason': 'Explicação completa',
                            }
                        ]
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(
            {
                'segments': [{'start': 0.0, 'end': 240.0, 'text': 'Explicação'}],
            },
            anthropic_client=mock_anthropic,
            fmt='curto',
        )

        assert len(result) == 1
        assert result[0]['start_time'] == 115.0
        assert result[0]['end_time'] == 160.0

    def test_shortform_completes_small_boundary_gap_to_30s(self):
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'moments': [
                            {
                                'start_time': 100.0,
                                'end_time': 129.4,
                                'score': 9,
                                'reason': 'Explicação quase completa',
                            }
                        ]
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(
            {'segments': [{'start': 0.0, 'end': 200.0, 'text': 'Explicação'}]},
            anthropic_client=mock_anthropic,
            fmt='curto',
        )

        assert len(result) == 1
        assert result[0]['start_time'] == 99.4
        assert result[0]['end_time'] == 129.4

    def test_shortform_normalizes_after_completing_transcript_boundary(self, sample_video_id):
        """A borda de fala é completada sem encurtar um Short dentro do limite."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'moments': [
                            {
                                'start_time': 10.0,
                                'end_time': 44.0,
                                'score': 9,
                                'reason': 'Explicação completa',
                            }
                        ]
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = mock_response
        transcript = {
            'video_id': 'vid001aaaaaa',
            'text': 'Explicação completa',
            'segments': [{'start': 10.0, 'end': 44.96, 'text': 'A fala termina aqui.'}],
        }

        result = select_moments(transcript, anthropic_client=mock_anthropic)

        assert len(result) == 1
        duration = result[0]['end_time'] - result[0]['start_time']
        assert 30 <= duration <= 45
        assert result[0]['end_time'] == pytest.approx(44.96)

    def test_shortform_keeps_exact_duration_after_boundary_adjustment(self, sample_video_id):
        """Uma frase vizinha pode ser ajustada, respeitando o teto de 45s."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'moments': [
                            {
                                'start_time': 500.0,
                                'end_time': 580.16,
                                'score': 9,
                                'reason': 'Análise sobre DeepSeek',
                            }
                        ]
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = mock_response
        transcript = {
            'video_id': 'vid001aaaaaa',
            'text': 'Texto',
            'segments': [
                {'start': 500.0, 'end': 578.08, 'text': 'Mudanças em vigor a partir do dia 17.'},
                {
                    'start': 578.08,
                    'end': 585.96,
                    'text': 'Então não vai ficar barato, apesar de...',
                },
            ],
        }

        result = select_moments(transcript, anthropic_client=mock_anthropic)

        assert len(result) == 1
        assert result[0]['end_time'] - result[0]['start_time'] == 45.0

    def test_end_time_snaps_to_segment_end_when_cut_is_inside_a_phrase(self):
        """Um fim no meio do bloco não pode truncar a última frase."""
        moments = [{'start_time': 100.0, 'end_time': 106.0, 'score': 9}]
        transcript_segments = [
            {'start': 100.0, 'end': 110.0, 'text': 'A explicação continua até o fim.'},
        ]

        result = complete_moment_boundaries(moments, transcript_segments)

        assert result[0]['start_time'] == 100.0
        assert result[0]['end_time'] == 110.0

    def test_end_time_continues_past_incomplete_transcript_block(self):
        """Uma oração que termina em vírgula avança até a continuação completa."""
        moments = [{'start_time': 500.0, 'end_time': 536.519, 'score': 9}]
        transcript_segments = [
            {
                'start': 534.120,
                'end': 536.519,
                'text': '>> Aham. que é diferente de você fazer,',
            },
            {
                'start': 536.519,
                'end': 538.480,
                'text': 'faça um algoritmo, faça um pequeno',
            },
            {
                'start': 538.480,
                'end': 540.760,
                'text': 'trecho. E aí eu fui rodar em todos eles.',
            },
        ]

        result = complete_moment_boundaries(moments, transcript_segments)

        assert result[0]['end_time'] == 540.760

    def test_end_time_continues_when_next_block_starts_lowercase(self):
        """Mesmo sem pontuação, a próxima linha minúscula revela continuação."""
        moments = [{'start_time': 500.0, 'end_time': 546.720, 'score': 9}]
        transcript_segments = [
            {'start': 542.920, 'end': 546.720, 'text': 'RTX 5090 da Nvidia e que é a melhor'},
            {'start': 546.720, 'end': 548.800, 'text': 'placa de vídeo que tem hoje no mercado.'},
        ]

        result = complete_moment_boundaries(moments, transcript_segments)

        assert result[0]['end_time'] == 548.800

    def test_longform_context_includes_intro_and_natural_closing_pause(self):
        """O longo recua para o início da fala e avança até a pausa do assunto."""
        moments = [
            {
                'start_time': 115.0,
                'end_time': 118.0,
                'score': 9,
                'reason': 'Análise completa',
            }
        ]
        transcript_segments = [
            {'start': 100.0, 'end': 110.0, 'text': 'Introdução do assunto.'},
            {'start': 110.4, 'end': 125.0, 'text': 'Desenvolvimento.'},
            {'start': 125.5, 'end': 140.0, 'text': 'Conclusão.'},
            {'start': 143.0, 'end': 150.0, 'text': 'Novo assunto.'},
        ]

        result = expand_longform_context(moments, transcript_segments)

        assert result[0]['start_time'] == 100.0
        assert result[0]['end_time'] == 140.0

    def test_longform_context_never_moves_end_before_selected_moment(self):
        """Uma pausa anterior não pode fazer o fechamento voltar para trás."""
        moments = [
            {
                'start_time': 200.0,
                'end_time': 245.0,
                'score': 9,
                'reason': 'Análise',
            }
        ]
        transcript_segments = [
            {'start': 0.0, 'end': 10.0, 'text': 'Abertura.'},
            {'start': 200.0, 'end': 230.0, 'text': 'Desenvolvimento.'},
            {'start': 231.0, 'end': 250.0, 'text': 'Fechamento.'},
        ]

        result = expand_longform_context(moments, transcript_segments)

        assert result[0]['end_time'] == 250.0

    def test_longform_clamps_hallucinated_bounds_and_keeps_minimum_duration(self):
        """Limites além da transcrição não podem produzir um longo curto demais."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'moments': [
                            {
                                'start_time': 9800.0,
                                'end_time': 10300.0,
                                'score': 9,
                                'reason': 'Análise longa',
                            }
                        ]
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = mock_response
        transcript = {
            'video_id': 'vid001aaaaaa',
            'text': 'Texto',
            'segments': [
                {'start': 0.0, 'end': 9000.0, 'text': 'Contexto.'},
                {'start': 9000.0, 'end': 9958.279, 'text': 'Conclusão.'},
            ],
        }

        result = select_moments(transcript, anthropic_client=mock_anthropic, fmt='longo')

        assert len(result) == 1
        assert result[0]['end_time'] <= 9958.279
        assert result[0]['end_time'] <= 9958.279
        assert result[0]['end_time'] - result[0]['start_time'] >= 420

    def test_shortform_entre_15s_e_30s_esticado(self, sample_video_id):
        """Momento de 15 s a 30 s é esticado até MIN_SHORTFORM_SECONDS, não descartado.

        Decisão do operador (15/09/2026): clip de 2-5 s não é assunto, mas a partir de 15 s
        já existe conteúdo e vale completar os 30 s com o contexto em volta.
        """
        mock_anthropic = MagicMock()
        moments = [
            {'start_time': 50.0, 'end_time': 70.0, 'score': 9, 'reason': 'Tem assunto, mas só 20s'}
        ]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': moments}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic, fmt='curto')

        assert len(result) == 1
        duracao = result[0]['end_time'] - result[0]['start_time']
        assert duracao == 30.0, f'esperava 30 s após o esticamento, veio {duracao}'
        # Esticou para os dois lados, sem sair do vídeo
        assert result[0]['start_time'] >= 0.0
        assert result[0]['start_time'] < 50.0

    def test_shortform_acima_do_teto_limitado(self, sample_video_id):
        """Momento maior que MAX_SHORTFORM_SECONDS é cortado no teto configurado."""
        mock_anthropic = MagicMock()
        moments = [
            {'start_time': 10.0, 'end_time': 300.0, 'score': 9, 'reason': 'Longo demais para short'}
        ]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': moments}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic, fmt='curto')

        assert len(result) == 1
        assert result[0]['end_time'] - result[0]['start_time'] == 45.0


class TestInsertMoments:
    def test_score_7_inserted(self, mock_db_conn):
        """AI-03: Momento com score=7 é inserido em generated_clips com status pending_cut."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 7, 'reason': 'Bom momento'}]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=moments
        )

        assert count == 1
        mock_db_conn.cursor().__enter__().execute.assert_called()
        call_args = mock_db_conn.cursor().__enter__().execute.call_args
        params = call_args[0][1]
        assert 'pending_cut' in params

    def test_score_6_discarded(self, mock_db_conn):
        """AI-03: Momento com score=6 não é inserido — count retorna 0."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 6, 'reason': 'Mediano'}]

        # Mock: lookup de destination_channel retorna target_niche/id
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},  # source_videos JOIN source_channels
            {'id': 1},  # destination_channels WHERE niche=futebol
        ]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=moments
        )

        assert count == 0
        # SELECTs são chamados (lookup do canal), mas INSERT não deve ocorrer
        insert_calls = [
            c
            for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 0, 'Momento com score < 7 não deve gerar INSERT'

    def test_overlap_keeps_higher_score(self, mock_db_conn):
        """AI-03: Dois momentos sobrepostos — apenas o de maior score é inserido."""
        overlapping = [
            {'start_time': 0.0, 'end_time': 400.0, 'score': 8, 'reason': 'Score maior'},
            {'start_time': 200.0, 'end_time': 600.0, 'score': 7, 'reason': 'Score menor — overlap'},
        ]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=overlapping
        )

        # Apenas 1 momento deve ser inserido (o de score 8)
        assert count == 1

    def test_registered_interval_is_not_inserted_again(self, mock_db_conn):
        """A trava no banco impede duplicata mesmo quando a IA ignora o histórico."""
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            {'start_time': 0.0, 'end_time': 60.0, 'status': 'published'},
        ]
        moments = [
            {'start_time': 0.0, 'end_time': 60.0, 'score': 10, 'reason': 'Repetido'},
            {'start_time': 100.0, 'end_time': 160.0, 'score': 8, 'reason': 'Novo'},
        ]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=moments
        )

        assert count == 1
        insert_calls = [
            call
            for call in cursor.execute.call_args_list
            if call.args and 'INSERT INTO generated_clips' in str(call.args[0])
        ]
        assert len(insert_calls) == 1
        assert 100.0 in insert_calls[0].args[1]

    def test_max_3_moments(self, mock_db_conn):
        """AI-03: Máximo 3 momentos inseridos mesmo se mais de 3 com score >= 7 forem passados."""
        many_moments = [
            {
                'start_time': i * 400.0,
                'end_time': i * 400.0 + 360.0,
                'score': 8,
                'reason': f'Momento {i}',
            }
            for i in range(5)  # 5 momentos não-sobrepostos com score 8
        ]

        # Mock: lookup de destination_channel
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},
            {'id': 2},
        ]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=many_moments
        )

        assert count <= 3


class TestInsertMomentsDestinationChannel:
    """MCAN-02: insert_selected_moments persiste destination_channel_id em generated_clips."""

    def test_destination_channel_id_persisted_in_insert(self, mock_db_conn):
        """MCAN-02: INSERT inclui destination_channel_id quando canal-destino existe para o nicho."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 8, 'reason': 'Gol'}]

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        # Primeiro SELECT: target_niche do canal de origem
        # Segundo SELECT: id do canal-destino para o nicho
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},  # source_videos JOIN source_channels
            {'id': 42},  # destination_channels WHERE niche='futebol'
        ]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=5, video_id='abc123', moments=moments
        )

        assert count == 1
        # Verificar que o INSERT inclui destination_channel_id
        insert_calls = [
            c
            for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 1, 'Deve haver exatamente 1 INSERT'
        params = insert_calls[0].args[1]
        assert 42 in params, (
            f'destination_channel_id=42 deve estar nos params do INSERT. Params: {params}'
        )

    def test_destination_must_use_the_source_prompt_profile(self, mock_db_conn):
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 8, 'reason': 'Insight'}]

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol', 'prompt_profile_id': 9},
            {'id': 42},
        ]

        assert insert_selected_moments(mock_db_conn, 5, 'abc123', moments) == 1

        destination_lookup = next(
            call
            for call in cursor.execute.call_args_list
            if 'SELECT id FROM destination_channels' in str(call.args[0])
        )
        assert 'prompt_profile_id = %s' in destination_lookup.args[0]
        assert destination_lookup.args[1] == (9,)

    def test_destination_channel_id_null_when_niche_is_null(self, mock_db_conn):
        """MCAN-02: Quando target_niche é NULL, destination_channel_id fica NULL (sem erro)."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 9, 'reason': 'Debate'}]

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        # Primeiro SELECT: target_niche = NULL
        cursor.fetchone.side_effect = [
            {'target_niche': None},  # sem nicho definido
        ]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=5, video_id='abc123', moments=moments
        )

        assert count == 1
        # INSERT deve ter None como destination_channel_id
        insert_calls = [
            c
            for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 1
        params = insert_calls[0].args[1]
        assert None in params, (
            f'destination_channel_id=None deve estar nos params. Params: {params}'
        )

    def test_destination_channel_id_null_when_no_active_destination(self, mock_db_conn):
        """MCAN-02: Quando não há canal-destino ativo para o nicho, destination_channel_id=NULL."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 8, 'reason': 'Análise'}]

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},  # nicho existe
            None,  # mas não há canal-destino ativo
        ]

        count = insert_selected_moments(
            mock_db_conn, source_video_id=5, video_id='abc123', moments=moments
        )

        assert count == 1
        insert_calls = [
            c
            for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 1
        params = insert_calls[0].args[1]
        assert None in params, (
            f'destination_channel_id=None quando sem destino ativo. Params: {params}'
        )
