"""
video_processor.py — Corte, legendas, thumbnail e processamento de clips.

Exporta:
  - cut_clip(source_path, start_time, end_time, output_path) -> str
  - generate_srt(transcript, start_time, end_time, srt_path) -> str
  - burn_subtitles(input_clip_path, srt_path, output_path) -> str
  - extract_thumbnail(clip_path, thumbnail_path, at_seconds=None) -> str
  - overlay_watermark(input_path, watermark_path, output_path) -> str
  - process_clip(conn, clip_id, anthropic_client=None) -> bool

Convenções:
  - FFmpeg é chamado via subprocess.run(check=True, capture_output=True)
  - Diretórios são constantes patcháveis em testes
  - conn: quem chama é responsável por fechar
"""
import json
import os
import subprocess
from datetime import datetime

from src.metadata_generator import generate_metadata, update_clip_metadata


VIDEOS_DIR = '/app/videos'
CLIPS_DIR = '/app/videos/clips'
THUMBNAILS_DIR = '/app/videos/thumbnails'
BRANDING_DIR = os.environ.get('BRANDING_DIR', '/app/branding')


def resolve_background_path(slug: str | None = None, niche: str | None = None) -> str | None:
    """Busca a imagem de background 1920x1080 do canal ou nicho."""
    candidates = []
    if slug:
        candidates.append(os.path.join(BRANDING_DIR, f'background-{slug}.png'))
    if niche:
        n = niche.lower()
        if 'fut' in n:
            candidates.append(os.path.join(BRANDING_DIR, 'background-futebol-em-cortes.png'))
        elif 'pol' in n:
            candidates.append(os.path.join(BRANDING_DIR, 'background-cortes-da-politica.png'))
        elif 'pod' in n:
            candidates.append(os.path.join(BRANDING_DIR, 'background-podcast-cortes.png'))

    # Fallback para execução local no host
    local_branding = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'branding'))
    if slug:
        candidates.append(os.path.join(local_branding, f'background-{slug}.png'))
    if niche:
        n = niche.lower()
        if 'fut' in n:
            candidates.append(os.path.join(local_branding, 'background-futebol-em-cortes.png'))
        elif 'pol' in n:
            candidates.append(os.path.join(local_branding, 'background-cortes-da-politica.png'))
        elif 'pod' in n:
            candidates.append(os.path.join(local_branding, 'background-podcast-cortes.png'))

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def resolve_default_template_config(channel_name: str = '', niche: str = '') -> dict:
    """Gera configuração padrão inteligente de template 9:16 baseada no nicho do canal."""
    n = (niche or '').lower()
    is_politica = 'pol' in n
    is_futebol = 'fut' in n
    return {
        'headerTitle': (channel_name or 'CANAL DE CORTES').upper(),
        'headerBadge': '🔴 DEBATE AO VIVO' if is_politica else ('⚽ LANCE DECISIVO' if is_futebol else '🎙️ CORTES EXCLUSIVOS'),
        'accentColor': '#E50914' if is_politica else ('#10B981' if is_futebol else '#8B5CF6'),
        'bgStyle': 'blur_dark',
        'subtitleColor': '#facc15',
        'ctaText': 'INSCREVA-SE NO CANAL',
    }


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def cut_clip(
    source_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    fmt: str = 'curto',
    template_config: dict | None = None,
    background_path: str | None = None,
) -> str:
    """Corta um trecho do vídeo fonte.

    fmt='curto' (padrão): converte pra vertical 1080x1920 (Shorts).
    fmt='longo': se background_path for fornecido, compõe o vídeo 16:9 na janela (1520x855 em x=320, y=72)
    sobre a imagem de background 1920x1080 do canal. Se não houver imagem de fundo, usa o blur vertical 9:16.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cfg = template_config or {}
    bg_style = cfg.get('bgStyle', 'blur_dark')

    duration = max(float(end_time) - float(start_time), 0.1)
    if fmt == 'longo':
        if duration > 1800:
            _log(f'Aviso: duração de corte longo ({duration}s) excede 1800s. Limitando a 1800s.')
            duration = 1800.0
            end_time = float(start_time) + duration
    else:
        if duration > 300:
            _log(f'Aviso: duração de corte curto ({duration}s) excede 300s. Limitando a 300s.')
            duration = 300.0
            end_time = float(start_time) + duration

    if fmt == 'longo':
        if background_path and os.path.exists(background_path):
            video_filter = (
                '[0:v]scale=1520:855:force_original_aspect_ratio=increase,crop=1520:855[fg];'
                '[1:v][fg]overlay=320:72,setsar=1'
            )
            input_args = [
                '-ss', str(start_time),
                '-to', str(end_time),
                '-i', source_path,
                '-loop', '1',
                '-i', background_path,
                '-t', str(duration),
            ]
            filter_args = ['-filter_complex', video_filter]
        else:
            if bg_style == 'blur_intense':
                blur_param = 'boxblur=35:10,eq=brightness=-0.35:contrast=0.90'
            else:
                blur_param = 'boxblur=25:5,eq=brightness=-0.30:contrast=0.95'

            video_filter = (
                f'[0:v]split=2[bg_in][fg_in];'
                f'[bg_in]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{blur_param}[bg];'
                f'[fg_in]scale=1080:-2[fg];'
                f'[bg][fg]overlay=0:(H-h)/2,setsar=1'
            )
            input_args = [
                '-ss', str(start_time),
                '-to', str(end_time),
                '-i', source_path,
            ]
            filter_args = ['-filter_complex', video_filter]
    else:
        video_filter = (
            'scale=1080:1920:force_original_aspect_ratio=increase,'
            'crop=1080:1920,'
            'setsar=1'
        )
        input_args = [
            '-ss', str(start_time),
            '-to', str(end_time),
            '-i', source_path,
        ]
        filter_args = ['-vf', video_filter]

    subprocess.run(
        [
            'ffmpeg',
            '-threads', '1',
            *input_args,
            *filter_args,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '24',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def generate_srt(transcript: dict, start_time: float, end_time: float, srt_path: str) -> str:
    """Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper."""
    os.makedirs(os.path.dirname(srt_path), exist_ok=True)
    cues = []

    for seg in transcript.get('segments', []):
        seg_start = float(seg['start'])
        seg_end = float(seg['end'])
        if seg_end <= start_time or seg_start >= end_time:
            continue

        cue_start = max(seg_start, start_time) - start_time
        cue_end = min(seg_end, end_time) - start_time
        text = str(seg.get('text', '')).strip()
        if not text:
            continue
        cues.append((cue_start, cue_end, text))

    with open(srt_path, 'w', encoding='utf-8') as f:
        for index, (cue_start, cue_end, text) in enumerate(cues, start=1):
            f.write(f'{index}\n')
            f.write(f'{_format_srt_time(cue_start)} --> {_format_srt_time(cue_end)}\n')
            f.write(f'{text}\n\n')

    return srt_path


def burn_subtitles(input_clip_path: str, srt_path: str, output_path: str, fmt: str = 'curto', template_config: dict | None = None) -> str:
    """Queima legendas SRT no clip usando FFmpeg."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cfg = template_config or {}
    color_hex = str(cfg.get('subtitleColor', '#facc15')).lower()
    if color_hex == '#ffffff':
        primary_color = '&H00FFFFFF'
    elif color_hex == '#38bdf8':
        primary_color = '&H00F8BD38'
    else:
        # Padrão amarelo ouro (#facc15 -> BBGGRR: 15CCFA)
        primary_color = '&H0015CCFA'

    if fmt == 'longo':
        subtitle_filter = (
            f"subtitles={srt_path}:"
            "force_style='Fontname=DejaVu Sans,Bold=1,Fontsize=30,"
            "PlayResX=1920,PlayResY=1080,"
            f"PrimaryColour={primary_color},OutlineColour=&H00000000,"
            "BackColour=&H60000000,"
            "BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=190'"
        )
    else:
        subtitle_filter = (
            f"subtitles={srt_path}:"
            "force_style='Fontname=DejaVu Sans,Bold=1,Fontsize=38,"
            "PlayResX=1080,PlayResY=1920,"
            f"PrimaryColour={primary_color},OutlineColour=&H00000000,"
            "BackColour=&H60000000,"
            "BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=200'"
        )

    subprocess.run(
        [
            'ffmpeg',
            '-threads', '1',
            '-i', input_clip_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '24',
            '-c:a', 'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def extract_thumbnail(
    clip_path: str,
    thumbnail_path: str,
    at_seconds: float = None,
    title: str | None = None,
    niche: str | None = None,
) -> str:
    """Extrai um frame do clip como thumbnail JPG e aplica tipografia de alto CTR estilo YouTube."""
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    if at_seconds is None:
        at_seconds = 1.0
    subprocess.run(
        [
            'ffmpeg',
            '-ss', str(at_seconds),
            '-i', clip_path,
            '-frames:v', '1',
            '-q:v', '2',
            thumbnail_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )

    if title:
        try:
            _apply_youtube_thumbnail_graphics(thumbnail_path, title, niche)
        except Exception as err:
            _log(f'[THUMBNAIL] Aviso: Não foi possível aplicar tipografia na thumbnail: {err}')

    return thumbnail_path


def _apply_youtube_thumbnail_graphics(thumbnail_path: str, title: str, niche: str | None = None):
    """Aplica tipografia profissional e vinheta de contraste na thumbnail gerada via Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
    except ImportError:
        _log('[THUMBNAIL] Pillow não disponível — mantendo frame bruto')
        return

    if not os.path.exists(thumbnail_path):
        return

    bg = Image.open(thumbnail_path).convert('RGB')
    bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)

    # 1. Tratamento profissional de imagem (Contraste + Saturação + Nitidez)
    bg = ImageEnhance.Contrast(bg).enhance(1.22)
    bg = ImageEnhance.Color(bg).enhance(1.25)
    bg = ImageEnhance.Sharpness(bg).enhance(1.15)

    is_pol = 'politic' in (niche or '').lower() or 'debate' in title.lower() or 'mbl' in title.lower()
    theme_accent = (0, 240, 255) if is_pol else (255, 229, 0)       # Ciano Neon (Política) ou Amarelo Ouro (Futebol)
    theme_second = (255, 229, 0) if is_pol else (255, 255, 255)     # Amarelo (Política) ou Branco (Futebol)
    badge_color = (229, 9, 20) if is_pol else (16, 185, 129)        # Vermelho ou Verde Esmeralda
    badge_text = '🔴 DEBATE AO VIVO' if is_pol else '⚽ LANCE DECISIVO'

    # 2. Vinheta gradiente escura na base e lateral para garantir contraste 100% perfeito
    overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    d_overlay = ImageDraw.Draw(overlay)
    # Gradiente inferior (onde fica o texto principal)
    for y in range(320, 720):
        factor = (y - 320) / 400.0
        alpha = int(220 * (factor ** 1.3))
        d_overlay.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
    # Gradiente lateral esquerdo sutil
    for x in range(0, 500):
        factor = 1.0 - (x / 500.0)
        alpha = int(140 * (factor ** 1.5))
        d_overlay.line([(x, 0), (x, 720)], fill=(0, 0, 0, alpha))
    bg.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(bg)

    # 3. Carregamento robusto de fontes do sistema (macOS e Linux/Docker)
    font_path = None
    for candidate in [
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/Library/Fonts/Arial Bold.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf',
    ]:
        if os.path.exists(candidate):
            font_path = candidate
            break

    def _get_font(size):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # 4. Borda / Glow Neon estético nas bordas do YouTube (Estilo MBL / Brigadeiro)
    border_color = (0, 240, 255, 180) if is_pol else (255, 215, 0, 180)
    border_overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    d_border = ImageDraw.Draw(border_overlay)
    d_border.rounded_rectangle([16, 16, 1264, 704], radius=14, outline=border_color, width=4)
    bg.paste(border_overlay, (0, 0), border_overlay)

    # 5. Badge Superior Esquerdo (com indicador circular vetorial sem depender de emojis de fonte)
    badge_label = 'DEBATE AO VIVO' if is_pol else 'LANCE DECISIVO'
    font_badge = _get_font(22)
    text_w = draw.textlength(badge_label, font=font_badge)
    badge_w = text_w + 54  # espaço para o ponto indicador + margens
    badge_h = 42
    bx, by = 48, 38
    draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=10, fill=badge_color)
    # Ponto circular indicador (branco ou vermelho pulsante)
    dot_color = (255, 255, 255) if is_pol else (255, 255, 255)
    draw.ellipse([bx + 14, by + 13, bx + 28, by + 27], fill=dot_color)
    draw.text((bx + 38, by + 7), badge_label, font=font_badge, fill='white')

    # 6. Processamento inteligente das linhas de texto (Gatilho de Alto CTR)
    clean_title = title.replace('"', '').replace("'", "").strip()
    parts = clean_title.split(':') if ':' in clean_title else clean_title.split(' - ') if ' - ' in clean_title else clean_title.split('! ')
    if len(parts) >= 2:
        main_text = parts[0].strip().upper()
        if not main_text.endswith('!') and not main_text.endswith('?'):
            main_text += '!'
        sub_text = ' '.join(parts[1:]).strip().upper()
    else:
        words = clean_title.strip().split()
        if len(words) <= 4:
            main_text = clean_title.upper()
            sub_text = ''
        else:
            mid = max(2, len(words) // 2)
            main_text = ' '.join(words[:mid]).upper()
            sub_text = ' '.join(words[mid:]).upper()

    if len(main_text) > 30:
        main_text = main_text[:27] + '...'
    if len(sub_text) > 34:
        sub_text = sub_text[:31] + '...'

    # Helper para desenhar texto com contorno 3D pesado (Stroke de 8px + Sombra)
    def _draw_stroked_text(x, y, text, font, fill_color, stroke_radius=8, shadow_offset=(4, 6)):
        if not text:
            return
        # Sombra profunda
        sx, sy = shadow_offset
        for dx in range(-stroke_radius, stroke_radius + 1):
            for dy in range(-stroke_radius, stroke_radius + 1):
                if dx * dx + dy * dy <= stroke_radius * stroke_radius:
                    draw.text((x + sx + dx, y + sy + dy), text, font=font, fill=(0, 0, 0))
        # Contorno preto nítido 360 graus
        for dx in range(-stroke_radius, stroke_radius + 1):
            for dy in range(-stroke_radius, stroke_radius + 1):
                if dx * dx + dy * dy <= stroke_radius * stroke_radius:
                    draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
        # Texto colorido frontal
        draw.text((x, y), text, font=font, fill=fill_color)

    # 7. Renderização da Linha 1 (Frase de Impacto Principal)
    font_main = _get_font(70 if len(main_text) <= 22 else 60)
    pos_y_main = 460 if sub_text else 540
    _draw_stroked_text(48, pos_y_main, main_text, font_main, fill_color=theme_accent, stroke_radius=8)

    # 8. Renderização da Linha 2 (Sub-gancho ou Tarja de Destaque)
    if sub_text:
        font_sub = _get_font(48 if len(sub_text) <= 26 else 40)
        pos_y_sub = pos_y_main + 88
        _draw_stroked_text(48, pos_y_sub, sub_text, font_sub, fill_color=theme_second, stroke_radius=7)

    # 9. Logo oficial do canal no Canto Superior Direito
    slug = 'cortes-da-politica' if is_pol else 'futebol-em-cortes'
    for candidate in [
        f'/app/branding/watermark-{slug}.png',
        f'branding/watermark-{slug}.png',
        f'/Users/alessandrobm1/develop/server/wordpress/canaldecortes/branding/watermark-{slug}.png',
    ]:
        if os.path.exists(candidate):
            try:
                wm = Image.open(candidate).convert('RGBA')
                wm = wm.resize((92, 92), Image.Resampling.LANCZOS)
                # Fundo circular escuro para a logo
                wm_bg = Image.new('RGBA', (100, 100), (0, 0, 0, 160))
                d_wmbg = ImageDraw.Draw(wm_bg)
                d_wmbg.ellipse([0, 0, 99, 99], fill=(0, 0, 0, 180), outline=border_color, width=2)
                bg.paste(wm_bg, (1280 - 100 - 40, 36), wm_bg)
                bg.paste(wm, (1280 - 92 - 44, 40), wm)
            except Exception as e:
                _log(f'[THUMBNAIL] Aviso: Logo watermark não aplicada: {e}')
            break

    bg.save(thumbnail_path, 'JPEG', quality=95)
    _log(f'[THUMBNAIL] Thumbnail estilizada gerada com sucesso: {thumbnail_path}')


def overlay_watermark(input_path: str, watermark_path: str, output_path: str) -> str:
    """Aplica watermark PNG no canto superior direito do clip via FFmpeg.

    Usa -filter_complex overlay=W-w-20:20 com dois inputs (clip + PNG alpha).
    Retorna input_path sem chamar FFmpeg se o watermark não existir (graceful degradation).
    """
    if not os.path.exists(watermark_path):
        _log(f'[WATERMARK] Arquivo não encontrado: {watermark_path} — pulo overlay')
        return input_path

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run(
        [
            'ffmpeg',
            '-i', input_path,        # [0] = clip vídeo
            '-i', watermark_path,    # [1] = PNG watermark
            '-filter_complex', 'overlay=W-w-20:20',  # canto sup direito, margem 20px
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-c:a', 'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def process_clip(conn, clip_id: int, anthropic_client=None) -> bool:
    """Processa um registro de generated_clips com status pending_cut.

    Pipeline: cut → generate_srt → burn_subtitles → overlay_watermark → extract_thumbnail
    O arquivo intermediário _subtitled.mp4 é removido após o watermark (ou rename).
    """
    try:
        clip = _fetch_clip(conn, clip_id)
        if clip is None:
            _log(f'Clip {clip_id} não encontrado')
            return False

        _update_clip_status(conn, clip_id, 'cutting')

        with open(clip['transcript_path'], 'r', encoding='utf-8') as f:
            transcript = json.load(f)

        raw_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}_raw.mp4')
        srt_path = os.path.join(CLIPS_DIR, f'{clip_id}.srt')
        subtitled_path = os.path.join(CLIPS_DIR, f'{clip_id}_subtitled.mp4')
        final_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}.mp4')
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f'{clip_id}.jpg')

        defaults = resolve_default_template_config(
            clip.get('destination_channel_name') or '',
            clip.get('destination_channel_niche') or '',
        )
        cfg = clip.get('template_config')
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except Exception:
                cfg = {}
        elif not isinstance(cfg, dict):
            cfg = {}

        merged_cfg = {**defaults, **cfg}

        slug = clip.get('destination_channel_slug')
        niche = clip.get('destination_channel_niche')
        fmt = clip.get('format') or 'curto'

        bg_path = resolve_background_path(slug=slug, niche=niche) if fmt == 'longo' else None

        cut_clip(
            clip['local_path'],
            clip['start_time'],
            clip['end_time'],
            raw_clip_path,
            fmt=fmt,
            template_config=merged_cfg,
            background_path=bg_path,
        )
        generate_srt(transcript, clip['start_time'], clip['end_time'], srt_path)
        burn_subtitles(raw_clip_path, srt_path, subtitled_path, fmt=fmt, template_config=merged_cfg)

        # Aplicar watermark se canal-destino tem slug configurado e formato curto (vídeo longo já tem branding integrado na moldura)
        if slug and fmt != 'longo':
            watermark_path = f'/app/branding/watermark-{slug}.png'
            # overlay_watermark retorna subtitled_path se arquivo de watermark não existir (graceful)
            result_path = overlay_watermark(subtitled_path, watermark_path, final_clip_path)
            if result_path == subtitled_path:
                # Watermark ausente: renomear para path final
                os.rename(subtitled_path, final_clip_path)
            else:
                # Watermark aplicado: remover intermediário
                if os.path.exists(subtitled_path):
                    os.remove(subtitled_path)
        else:
            # Sem canal-destino ou vídeo longo: renomear arquivo legendado para path final
            os.rename(subtitled_path, final_clip_path)

        metadata = generate_metadata(_build_clip_context(clip, transcript), anthropic_client=anthropic_client)
        update_clip_metadata(conn, clip_id, metadata)
        title = (metadata.get('title') or clip.get('title') or clip.get('source_title') or 'CORTES EXCLUSIVOS').strip()

        duration = max(float(clip['end_time']) - float(clip['start_time']), 1.0)
        # Para vídeo longo 16:9, captura o frame limpo do vídeo original para qualidade HD na capa
        thumb_source = clip.get('local_path') if (fmt == 'longo' and clip.get('local_path') and os.path.exists(clip['local_path'])) else final_clip_path
        at_sec = float(clip['start_time']) + min(3.0, duration * 0.25) if thumb_source == clip.get('local_path') else min(2.0, duration * 0.25)

        extract_thumbnail(
            thumb_source,
            thumbnail_path,
            at_seconds=at_sec,
            title=title,
            niche=niche,
        )

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE generated_clips '
                'SET clip_path=%s, thumbnail_path=%s '
                'WHERE id=%s',
                (final_clip_path, thumbnail_path, clip_id),
            )
        conn.commit()

        _update_clip_status(conn, clip_id, 'pending')
        _log(f'Clip {clip_id} processado: {final_clip_path}')
        return True

    except Exception as exc:
        _log(f'Erro ao processar clip {clip_id}: {exc}')
        try:
            _update_clip_status(conn, clip_id, 'failed')
        except Exception:
            pass
        return False


def _fetch_clip(conn, clip_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.start_time, gc.end_time, gc.score, gc.reason, '
            'sv.youtube_video_id, sv.title AS source_title, sv.local_path, sv.transcript_path, sv.format, '
            'dc.slug AS destination_channel_slug, dc.name AS destination_channel_name, dc.niche AS destination_channel_niche, dc.template_config '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'LEFT JOIN destination_channels dc ON dc.id = gc.destination_channel_id '
            'WHERE gc.id = %s',
            (clip_id,),
        )
        return cur.fetchone()


def _update_clip_status(conn, clip_id: int, status: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips SET status=%s WHERE id=%s',
            (status, clip_id),
        )
    conn.commit()


def _build_clip_context(clip: dict, transcript: dict) -> dict:
    start_time = float(clip['start_time'])
    end_time = float(clip['end_time'])
    excerpt_lines = []
    for seg in transcript.get('segments', []):
        seg_start = float(seg['start'])
        seg_end = float(seg['end'])
        if seg_end > start_time and seg_start < end_time:
            excerpt_lines.append(str(seg.get('text', '')).strip())

    return {
        'source_title': clip.get('source_title') or '',
        'reason': clip.get('reason') or '',
        'score': clip.get('score'),
        'start_time': start_time,
        'end_time': end_time,
        'niche': clip.get('destination_channel_niche') or 'futebol',
        'format': clip.get('format') or 'curto',
        'transcript_excerpt': ' '.join(line for line in excerpt_lines if line),
    }


def _format_srt_time(seconds: float) -> str:
    milliseconds_total = int(round(seconds * 1000))
    hours = milliseconds_total // 3_600_000
    remainder = milliseconds_total % 3_600_000
    minutes = remainder // 60_000
    remainder %= 60_000
    secs = remainder // 1000
    millis = remainder % 1000
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}'
