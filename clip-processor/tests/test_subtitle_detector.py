"""
test_subtitle_detector.py — Detecção de legenda já queimada no vídeo fonte.

O detector cruza o OCR do rodapé com a transcrição, então os testes simulam o
par FFmpeg + tesseract: cada amostra do trecho devolve um texto "lido" da tela.
"""

import subprocess

import pytest

from src.subtitle_detector import (
    SAMPLE_COUNT,
    _significant_words,
    _spoken_words,
    has_burned_subtitles,
)

# Clip 100→160 s: as amostras caem em 105, 115, 125, 135, 145 e 155 s.
FALAS = [
    'Governo aprovou a reforma tributária completa',
    'Mercado reagiu com forte volatilidade cambial',
    'Ninguém explicou direito o impacto nos estados',
    'Prefeitura prometeu revisar o orçamento municipal',
    'Empresário reclamou da burocracia excessiva',
    'Especialista alertou sobre inflação persistente',
]
TRANSCRIPT = {
    'segments': [
        {'start': 100.0 + index * 10, 'end': 110.0 + index * 10, 'text': texto}
        for index, texto in enumerate(FALAS)
    ]
}
BANNER = 'Patrocínio Supermercados BH — Sócio Torcedor'


@pytest.fixture
def screen_text(mocker):
    """Faz o detector "ler" os textos dados, um por amostra, sem chamar FFmpeg/tesseract."""
    mocker.patch('src.subtitle_detector.os.path.isfile', return_value=True)
    mocker.patch('src.subtitle_detector.shutil.which', return_value='/usr/bin/tesseract')
    mock_run = mocker.patch('src.subtitle_detector.subprocess.run')

    def _serve(textos):
        fila = list(textos)

        def _fake_run(command, **kwargs):
            if command[0] == 'ffmpeg':
                return mocker.Mock(returncode=0, stdout=b'')
            texto = fila.pop(0) if fila else ''
            return mocker.Mock(returncode=0, stdout=texto.encode('utf-8'))

        mock_run.side_effect = _fake_run
        return mock_run

    return _serve


class TestHasBurnedSubtitles:
    def test_rodape_que_repete_a_fala_e_legenda_queimada(self, screen_text):
        screen_text(FALAS)

        assert has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0) is True

    def test_uma_leitura_ocr_falha_ainda_decide_pela_maioria(self, screen_text):
        # Um quadro sem texto legível não derruba a evidência dos outros cinco.
        screen_text([FALAS[0], '', *FALAS[2:]])

        assert has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0) is True

    def test_banner_de_patrocinador_nao_conta_como_legenda(self, screen_text):
        screen_text([BANNER] * SAMPLE_COUNT)

        assert has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0) is False

    def test_texto_lido_em_voz_alta_em_parte_do_trecho_nao_basta(self, screen_text):
        # Apresentador compartilha a tela e lê o texto em voz alta por alguns
        # segundos: bate com a transcrição no meio do trecho, não no trecho todo.
        screen_text([BANNER, BANNER, FALAS[2], FALAS[3], FALAS[4], BANNER])

        assert has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0) is False

    def test_sem_tesseract_mantem_a_legenda_queimada(self, mocker):
        mocker.patch('src.subtitle_detector.os.path.isfile', return_value=True)
        mocker.patch('src.subtitle_detector.shutil.which', return_value=None)
        mock_run = mocker.patch('src.subtitle_detector.subprocess.run')

        assert has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0) is False
        mock_run.assert_not_called()

    def test_falha_do_ffmpeg_mantem_a_legenda_queimada(self, mocker):
        mocker.patch('src.subtitle_detector.os.path.isfile', return_value=True)
        mocker.patch('src.subtitle_detector.shutil.which', return_value='/usr/bin/tesseract')
        mocker.patch(
            'src.subtitle_detector.subprocess.run',
            side_effect=subprocess.CalledProcessError(1, 'ffmpeg'),
        )

        assert has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0) is False

    def test_fonte_ausente_nao_chama_ffmpeg(self, mocker):
        mock_run = mocker.patch('src.subtitle_detector.subprocess.run')

        assert has_burned_subtitles('/app/videos/sumiu.mp4', TRANSCRIPT, 100.0, 160.0) is False
        mock_run.assert_not_called()

    def test_transcricao_vazia_nao_decide_nada(self, screen_text):
        screen_text(FALAS)

        assert (
            has_burned_subtitles('/app/videos/fonte.mp4', {'segments': []}, 100.0, 160.0) is False
        )

    def test_flag_de_ambiente_desliga_a_deteccao(self, mocker, monkeypatch):
        monkeypatch.setenv('BURNED_SUBTITLE_DETECTION', 'false')
        mock_run = mocker.patch('src.subtitle_detector.subprocess.run')

        assert has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0) is False
        mock_run.assert_not_called()

    def test_le_a_faixa_inferior_e_usa_o_idioma_portugues(self, screen_text):
        mock_run = screen_text(FALAS)

        has_burned_subtitles('/app/videos/fonte.mp4', TRANSCRIPT, 100.0, 160.0)

        comandos = [call.args[0] for call in mock_run.call_args_list]
        ffmpeg = [cmd for cmd in comandos if cmd[0] == 'ffmpeg']
        tesseract = [cmd for cmd in comandos if cmd[0] == 'tesseract']
        assert len(ffmpeg) == SAMPLE_COUNT
        assert 'crop=iw:ih*0.5:0:ih*0.5' in ffmpeg[0][ffmpeg[0].index('-vf') + 1]
        # As amostras cobrem o trecho inteiro, não só o começo.
        instantes = [float(cmd[cmd.index('-ss') + 1]) for cmd in ffmpeg]
        assert instantes[0] == pytest.approx(105.0)
        assert instantes[-1] == pytest.approx(155.0)
        assert tesseract[0][tesseract[0].index('-l') + 1] == 'por'


class TestNormalizacao:
    def test_acentos_e_pontuacao_nao_atrapalham_o_casamento(self):
        assert 'tributaria' in _significant_words('Reforma tributária, enfim!')

    def test_palavras_curtas_sao_descartadas(self):
        # "que", "não" e "de" aparecem em qualquer texto da tela.
        assert _significant_words('que não é de nós') == set()

    def test_so_conta_a_fala_em_torno_do_instante(self):
        palavras = _spoken_words(TRANSCRIPT, 115.0)

        assert 'volatilidade' in palavras
        assert 'burocracia' not in palavras
