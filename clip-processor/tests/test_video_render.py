"""
test_video_render.py — Lote 7: modos de render, áudio dinâmico, Short em passe único
e contrato técnico de mídia.
"""
import json
import shutil
import subprocess

import pytest

from src import media_contract, video_quality
from src.media_contract import MediaContractError, shorts_max_duration, validate_short_media
from src.video_processor import cut_clip, process_clip, render_short_clip
from src.video_quality import (
    audio_encoder_options,
    dynamic_audio_filter,
    video_encoder_options,
    video_render_mode,
)


@pytest.fixture(autouse=True)
def _env_limpo(monkeypatch):
    for name in (
        'VIDEO_RENDER_MODE', 'FFMPEG_PRESET', 'FFMPEG_CRF', 'FFMPEG_THREADS',
        'AUDIO_LOUDNORM', 'SHORTS_MAX_DURATION_SECONDS', 'SHORTS_SINGLE_PASS',
    ):
        monkeypatch.delenv(name, raising=False)


def _opt(options, flag):
    return options[options.index(flag) + 1]


class TestVideoQuality:
    def test_padrao_preserva_o_encode_atual_da_master(self):
        assert video_render_mode() == 'padrao'
        opts = video_encoder_options()
        assert _opt(opts, '-preset') == 'ultrafast'
        assert _opt(opts, '-crf') == '24'
        assert _opt(opts, '-threads') == '1'
        assert _opt(audio_encoder_options(), '-b:a') == '128k'

    @pytest.mark.parametrize('valor', ['economia', 'fast', 'ECONOMIA'])
    def test_modo_economia_usa_veryfast(self, monkeypatch, valor):
        monkeypatch.setenv('VIDEO_RENDER_MODE', valor)
        opts = video_encoder_options()
        assert _opt(opts, '-preset') == 'veryfast'
        assert _opt(opts, '-crf') == '16'

    @pytest.mark.parametrize('valor', ['quality', 'maximo'])
    def test_modo_qualidade_maxima_e_opt_in(self, monkeypatch, valor):
        monkeypatch.setenv('VIDEO_RENDER_MODE', valor)
        opts = video_encoder_options()
        assert _opt(opts, '-preset') == 'slow'
        assert _opt(opts, '-crf') == '14'
        assert _opt(opts, '-profile:v') == 'high'
        assert _opt(opts, '-pix_fmt') == 'yuv420p'
        assert _opt(audio_encoder_options(), '-b:a') == '320k'

    def test_modo_desconhecido_cai_no_padrao(self, monkeypatch):
        monkeypatch.setenv('VIDEO_RENDER_MODE', 'turbo')
        assert video_render_mode() == 'padrao'

    def test_overrides_finos_vencem_o_modo(self, monkeypatch):
        monkeypatch.setenv('VIDEO_RENDER_MODE', 'economia')
        monkeypatch.setenv('FFMPEG_PRESET', 'medium')
        monkeypatch.setenv('FFMPEG_CRF', '20')
        monkeypatch.setenv('FFMPEG_THREADS', '4')
        opts = video_encoder_options()
        assert (_opt(opts, '-preset'), _opt(opts, '-crf'), _opt(opts, '-threads')) == ('medium', '20', '4')

    def test_audio_dinamico_tem_loudnorm_e_fades(self):
        flt = dynamic_audio_filter(30.0)
        assert 'loudnorm=I=-14' in flt
        assert 'afade=t=in' in flt
        assert 'st=29.80' in flt

    def test_audio_dinamico_pode_ser_desligado(self, monkeypatch):
        monkeypatch.setenv('AUDIO_LOUDNORM', '0')
        assert dynamic_audio_filter(30.0) is None


class TestRenderShortClip:
    def test_uma_unica_chamada_ffmpeg_com_legenda_e_watermark(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')
        wm = tmp_path / 'wm.png'
        wm.write_bytes(b'png')

        render_short_clip(
            '/app/videos/src.mp4', 100.0, 130.0, str(tmp_path / 'out.mp4'),
            subtitle_path='/app/videos/clips/1.srt', watermark_path=str(wm),
        )

        assert mock_run.call_count == 1
        cmd = mock_run.call_args.args[0]
        graph = cmd[cmd.index('-filter_complex') + 1]
        assert 'crop=1080:1920' in graph
        assert 'subtitles=/app/videos/clips/1.srt' in graph
        assert 'overlay=W-w-20:20' in graph
        assert cmd.count('-c:v') == 1  # um único encode de vídeo
        assert cmd[cmd.index('-ss') + 1] == '100.0'
        assert cmd[cmd.index('-to') + 1] == '130.0'
        assert '-af' in cmd and 'loudnorm' in cmd[cmd.index('-af') + 1]

    def test_sem_legenda_nem_watermark_so_enquadra(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')

        render_short_clip('/app/videos/src.mp4', 0.0, 40.0, str(tmp_path / 'out.mp4'))

        cmd = mock_run.call_args.args[0]
        graph = cmd[cmd.index('-filter_complex') + 1]
        assert 'subtitles' not in graph and 'overlay' not in graph

    def test_watermark_ausente_e_ignorado(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')

        render_short_clip(
            '/app/videos/src.mp4', 0.0, 40.0, str(tmp_path / 'out.mp4'),
            watermark_path='/nao/existe.png',
        )

        cmd = mock_run.call_args.args[0]
        assert 'overlay' not in cmd[cmd.index('-filter_complex') + 1]
        assert cmd.count('-i') == 1

    def test_usa_cor_de_legenda_do_template(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')

        render_short_clip(
            '/app/videos/src.mp4', 0.0, 40.0, str(tmp_path / 'out.mp4'),
            subtitle_path='/x.srt', template_config={'subtitleColor': '#ffffff'},
        )

        graph = mock_run.call_args.args[0][mock_run.call_args.args[0].index('-filter_complex') + 1]
        assert 'PrimaryColour=&H00FFFFFF' in graph

    def test_teto_de_duracao_padrao_180s(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')

        render_short_clip('/app/videos/src.mp4', 10.0, 400.0, str(tmp_path / 'out.mp4'))

        cmd = mock_run.call_args.args[0]
        assert float(cmd[cmd.index('-to') + 1]) == 190.0

    def test_teto_configuravel_45s(self, tmp_path, mocker, monkeypatch):
        monkeypatch.setenv('SHORTS_MAX_DURATION_SECONDS', '45')
        mock_run = mocker.patch('src.video_processor.subprocess.run')

        render_short_clip('/app/videos/src.mp4', 10.0, 100.0, str(tmp_path / 'out.mp4'))

        cmd = mock_run.call_args.args[0]
        assert float(cmd[cmd.index('-to') + 1]) == 55.0

    def test_cut_clip_aplica_encoder_do_modo_e_audio_dinamico(self, tmp_path, mocker, monkeypatch):
        monkeypatch.setenv('VIDEO_RENDER_MODE', 'economia')
        mock_run = mocker.patch('src.video_processor.subprocess.run')

        cut_clip('/app/videos/src.mp4', 0.0, 60.0, str(tmp_path / 'c.mp4'))

        cmd = mock_run.call_args.args[0]
        assert _opt(cmd, '-preset') == 'veryfast'
        assert 'loudnorm' in cmd[cmd.index('-af') + 1]


class TestMediaContract:
    def _fake_probe(self, mocker, **info):
        base = {'duration': 30.0, 'width': 1080, 'height': 1920, 'is_vertical': True}
        base.update(info)
        mocker.patch('src.media_contract.probe_media', return_value=base)

    def test_teto_padrao_e_180(self):
        assert shorts_max_duration() == 180.0

    def test_teto_env_invalido_cai_no_padrao(self, monkeypatch):
        monkeypatch.setenv('SHORTS_MAX_DURATION_SECONDS', 'abc')
        assert shorts_max_duration() == 180.0

    def test_aceita_clip_de_15_a_180s(self, mocker):
        for dur in (15.0, 29.0, 120.0, 180.2):
            self._fake_probe(mocker, duration=dur)
            assert validate_short_media('/x.mp4')['duration'] == dur

    def test_rejeita_acima_do_teto(self, mocker):
        self._fake_probe(mocker, duration=181.0)
        with pytest.raises(MediaContractError):
            validate_short_media('/x.mp4')

    def test_rejeita_abaixo_do_piso_absoluto(self, mocker):
        self._fake_probe(mocker, duration=3.0)
        with pytest.raises(MediaContractError):
            validate_short_media('/x.mp4')

    def test_teto_45s_por_env(self, mocker, monkeypatch):
        monkeypatch.setenv('SHORTS_MAX_DURATION_SECONDS', '45')
        self._fake_probe(mocker, duration=60.0)
        with pytest.raises(MediaContractError):
            validate_short_media('/x.mp4')

    def test_rejeita_nao_vertical(self, mocker):
        self._fake_probe(mocker, width=1920, height=1080, is_vertical=False)
        with pytest.raises(MediaContractError):
            validate_short_media('/x.mp4')

    def test_ffprobe_ausente(self, mocker):
        mocker.patch('src.media_contract.subprocess.run', side_effect=FileNotFoundError)
        with pytest.raises(MediaContractError):
            media_contract.probe_media('/x.mp4')


SAMPLE_TRANSCRIPT = {'segments': [{'start': 100.0, 'end': 110.0, 'text': 'fala do corte'}]}


class TestProcessClipPassoUnico:
    def _clip(self, slug):
        return {
            'id': 30, 'source_video_id': 1, 'youtube_video_id': 'v', 'source_title': 'T',
            'local_path': '/app/videos/source.mp4', 'start_time': 100.0, 'end_time': 130.0,
            'score': 9, 'reason': 'r', 'destination_channel_slug': slug, 'format': 'curto',
        }

    def _prepare(self, tmp_path, mock_db_conn, mocker, slug):
        tp = tmp_path / 't.json'
        tp.write_text(json.dumps(SAMPLE_TRANSCRIPT), encoding='utf-8')
        row = self._clip(slug)
        row['transcript_path'] = str(tp)
        mock_db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = row
        mocker.patch('src.video_processor.generate_metadata', return_value={'title': 'T'})
        mocker.patch('src.video_processor.update_clip_metadata')
        mocker.patch('src.video_processor.extract_thumbnail')
        mocker.patch('src.video_processor.validate_short_media', return_value={})
        mocker.patch('src.video_processor.generate_srt')
        mocker.patch('src.video_processor.has_burned_subtitles', return_value=False)
        return {
            'render': mocker.patch('src.video_processor.render_short_clip'),
            'cut': mocker.patch('src.video_processor.cut_clip'),
            'burn': mocker.patch('src.video_processor.burn_subtitles'),
            'wm': mocker.patch('src.video_processor.overlay_watermark'),
        }

    def test_curto_usa_um_render_e_nenhum_dos_tres_passes(self, tmp_path, mock_db_conn, mocker):
        m = self._prepare(tmp_path, mock_db_conn, mocker, 'canal-x')

        assert process_clip(mock_db_conn, 30) is True

        m['render'].assert_called_once()
        kwargs = m['render'].call_args.kwargs
        assert kwargs['watermark_path'] == '/app/branding/watermark-canal-x.png'
        assert kwargs['subtitle_path'].endswith('30.srt')
        m['cut'].assert_not_called()
        m['burn'].assert_not_called()
        m['wm'].assert_not_called()

    def test_legenda_ja_queimada_na_fonte_nao_e_repetida(self, tmp_path, mock_db_conn, mocker):
        m = self._prepare(tmp_path, mock_db_conn, mocker, None)
        mocker.patch('src.video_processor.has_burned_subtitles', return_value=True)

        assert process_clip(mock_db_conn, 30) is True

        assert m['render'].call_args.kwargs['subtitle_path'] is None

    def test_contrato_violado_marca_clip_failed(self, tmp_path, mock_db_conn, mocker):
        self._prepare(tmp_path, mock_db_conn, mocker, None)
        mocker.patch('src.video_processor.validate_short_media', side_effect=MediaContractError('ruim'))

        assert process_clip(mock_db_conn, 30) is False
        cur = mock_db_conn.cursor.return_value.__enter__.return_value
        assert any('failed' in str(c) for c in cur.execute.call_args_list)

    def test_flag_desliga_passe_unico(self, tmp_path, mock_db_conn, mocker, monkeypatch):
        monkeypatch.setenv('SHORTS_SINGLE_PASS', '0')
        m = self._prepare(tmp_path, mock_db_conn, mocker, None)
        mocker.patch('src.video_processor.os.rename')

        assert process_clip(mock_db_conn, 30) is True

        m['render'].assert_not_called()
        m['cut'].assert_called_once()
        m['burn'].assert_called_once()

    def test_longo_nao_usa_passe_unico(self, tmp_path, mock_db_conn, mocker):
        m = self._prepare(tmp_path, mock_db_conn, mocker, None)
        cur = mock_db_conn.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = {**cur.fetchone.return_value, 'format': 'longo'}
        mocker.patch('src.video_processor.os.rename')

        assert process_clip(mock_db_conn, 30) is True

        m['render'].assert_not_called()
        m['cut'].assert_called_once()


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='ffmpeg indisponível')
class TestRenderReal:
    """Render de verdade com vídeo sintético (roda na imagem do clip-processor)."""

    def test_short_real_sai_1080x1920_e_passa_no_contrato(self, tmp_path):
        src = tmp_path / 'src.mp4'
        subprocess.run(
            [
                'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=size=640x360:rate=25',
                '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '8',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', str(src), '-y',
            ],
            check=True, capture_output=True,
        )
        out = tmp_path / 'short.mp4'

        render_short_clip(str(src), 1.0, 7.0, str(out))

        info = validate_short_media(str(out))
        assert (info['width'], info['height']) == (1080, 1920)
        assert 5.5 < info['duration'] < 6.5
