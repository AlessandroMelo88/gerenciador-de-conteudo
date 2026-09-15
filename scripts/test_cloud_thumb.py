import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def generate_cloud_thumbnail(
    base_frame_path: str,
    output_path: str,
    title: str,
    niche: str = 'politica',
    badge_text: str = None,
    watermark_path: str = None
):
    # 1. Base 1280x720
    if os.path.exists(base_frame_path):
        bg = Image.open(base_frame_path).convert('RGB')
        bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)
    else:
        bg = Image.new('RGB', (1280, 720), (12, 18, 32))

    # Realce de cores e contraste do fundo (estilo YouTube de alta retenção)
    bg = ImageEnhance.Contrast(bg).enhance(1.22)
    bg = ImageEnhance.Color(bg).enhance(1.20)
    bg = ImageEnhance.Sharpness(bg).enhance(1.15)

    n = (niche or '').lower()
    is_pol = 'pol' in n or 'debate' in n or 'fatos' in n
    is_fut = 'fut' in n or 'bola' in n
    is_mon = 'monetiz' in n or '3g' in n or 'market' in n

    # 2. Fonte de Ultra Destaque (Anton / Arial Black / Impact)
    font_path = None
    for cand in [
        'branding/fonts/Anton-Regular.ttf',
        '/System/Library/Fonts/Supplemental/Arial Black.ttf',
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        '/Library/Fonts/Arial Black.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ]:
        if os.path.exists(cand):
            font_path = cand
            break

    def get_font(size: int):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # 3. Processamento do Título em Linha 1 e Linha 2
    clean_title = title.replace('"', '').replace("'", "").strip()
    parts = clean_title.split(':') if ':' in clean_title else clean_title.split(' - ') if ' - ' in clean_title else clean_title.split('! ')
    if len(parts) >= 2:
        text1 = parts[0].strip().upper()
        if not text1.endswith('!') and not text1.endswith('?'):
            text1 += '!'
        text2 = ' '.join(parts[1:]).strip().upper()
    else:
        words = clean_title.strip().split()
        if len(words) <= 4:
            text1 = clean_title.upper()
            text2 = 'DECISÃO URGENTE!' if is_pol else ('GOLAÇO HISTÓRICO!' if is_fut else 'MÉTODO REVELADO!')
        else:
            mid = max(2, len(words) // 2)
            text1 = ' '.join(words[:mid]).upper() + '!'
            text2 = ' '.join(words[mid:]).upper()

    # Cores e Estilos por Nicho
    if is_pol:
        # Fatos & Debates: Branco + Ciano Elétrico Neon (#00E5FF)
        color_line1 = (255, 255, 255)       # Branco Puro
        color_line2 = (0, 225, 255)         # Ciano Neon
        badge_label = badge_text or 'FATOS & DEBATES'
        badge_dot_color = (239, 68, 68)     # Vermelho vivo
        badge_bg = (180, 15, 25, 240)
        glow_color = (0, 210, 255, 170)
        neon_border = (0, 225, 255, 230)
        wm_default = 'branding/watermark-fatos-e-debates.png'
    elif is_fut:
        # Futebol em Cortes: Branco + Amarelo Ouro Elétrico (#FFE100)
        color_line1 = (255, 255, 255)       # Branco Puro
        color_line2 = (255, 225, 0)         # Amarelo Ouro
        badge_label = badge_text or 'LANCE DECISIVO'
        badge_dot_color = (34, 197, 94)     # Verde neon
        badge_bg = (16, 140, 75, 240)
        glow_color = (34, 197, 94, 170)
        neon_border = (34, 197, 94, 230)
        wm_default = 'branding/watermark-futebol-em-cortes.png'
    else:
        # Monetização 3G: Branco + Ouro / Amarelo
        color_line1 = (255, 255, 255)
        color_line2 = (255, 215, 0)
        badge_label = badge_text or 'MONETIZAÇÃO 3G'
        badge_dot_color = (168, 85, 247)
        badge_bg = (109, 40, 217, 240)
        glow_color = (168, 85, 247, 170)
        neon_border = (234, 179, 8, 230)
        wm_default = None

    # 4. Cálculo dinâmico de fontes (TAMANHO GIGANTE de alto CTR)
    max_w = 930
    font_size1 = 76
    f1 = get_font(font_size1)
    dummy = ImageDraw.Draw(bg)
    while dummy.textlength(text1, font=f1) > max_w and font_size1 > 42:
        font_size1 -= 2
        f1 = get_font(font_size1)

    font_size2 = 82
    f2 = get_font(font_size2)
    while dummy.textlength(text2, font=f2) > max_w and font_size2 > 42:
        font_size2 -= 2
        f2 = get_font(font_size2)

    # 5. EFEITO DE NUVEM DE SOMBRA (SHADOW CLOUD / SMOKE EFFECT)
    # Sem caixa quadrada! Uma névoa/nuvem escura orgânica e suave
    cloud = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    d_cloud = ImageDraw.Draw(cloud)

    base_x = 75
    base_y = 475

    # Desenha manchas orgânicas de fumaça preta com alta opacidade no centro
    d_cloud.ellipse([-100, 360, 1380, 750], fill=(0, 0, 0, 235))
    d_cloud.ellipse([30, 420, 1150, 720], fill=(4, 8, 16, 250))
    d_cloud.ellipse([base_x - 50, base_y - 30, base_x + max_w + 120, base_y + 220], fill=(0, 0, 0, 240))

    # Vinheta extra de contraste suave
    for y in range(350, 720):
        factor = (y - 350) / 370.0
        alpha = int(220 * (factor ** 1.3))
        d_cloud.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))

    # Desfoque gaussiano suave (efeito de nuvem/fumaça sem bordas retas)
    cloud = cloud.filter(ImageFilter.GaussianBlur(radius=40))
    bg.paste(cloud, (0, 0), cloud)

    # 6. RENDERIZAÇÃO DO TEXTO EM CAMADA SEPARADA (COM LEVE ANGULAÇÃO DIAGONAL -3.0°)
    text_canvas_w = 1200
    text_canvas_h = 300
    text_img = Image.new('RGBA', (text_canvas_w, text_canvas_h), (0, 0, 0, 0))
    d_text = ImageDraw.Draw(text_img)

    def draw_text_with_depth(d, x, y, text, font, fill_color, stroke_w=8, depth=7):
        # Sombra 3D projetada para baixo e direita
        for offset in range(1, depth + 1):
            d.text((x + offset, y + offset + 2), text, font=font, fill=(0, 0, 0, 255))
        
        # Contorno 360 graus grosso e limpo
        for dx in range(-stroke_w, stroke_w + 1):
            for dy in range(-stroke_w, stroke_w + 1):
                if dx * dx + dy * dy <= stroke_w * stroke_w:
                    d.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))

        # Texto frontal vibrante
        d.text((x, y), text, font=font, fill=fill_color)

    y1 = 12
    draw_text_with_depth(d_text, 10, y1, text1, f1, color_line1, stroke_w=7, depth=6)

    bbox1 = f1.getbbox(text1)
    h1 = (bbox1[3] - bbox1[1]) if bbox1 else font_size1
    y2 = y1 + h1 + 18
    draw_text_with_depth(d_text, 10, y2, text2, f2, color_line2, stroke_w=8, depth=7)

    # Angulação diagonal de -3.0 graus
    angle = -3.0
    rotated_text = text_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    bg.paste(rotated_text, (base_x, base_y - 25), rotated_text)

    # 7. EFEITO DA BOLA / BRASÃO COM AURA NEON (No canto direito)
    circle_size = 145
    ball_x = 1075
    ball_y = 515

    # Halo / Nuvem de brilho neon da bola
    ball_glow = Image.new('RGBA', (circle_size + 60, circle_size + 60), (0, 0, 0, 0))
    d_bglow = ImageDraw.Draw(ball_glow)
    d_bglow.ellipse([10, 10, circle_size + 50, circle_size + 50], fill=glow_color)
    ball_glow = ball_glow.filter(ImageFilter.GaussianBlur(radius=20))
    bg.paste(ball_glow, (ball_x - 30, ball_y - 30), ball_glow)

    # Emblema com anéis concêntricos (dourado + neon)
    emblem_layer = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
    d_emb = ImageDraw.Draw(emblem_layer)
    d_emb.ellipse([4, 4, circle_size - 4, circle_size - 4], fill=(8, 12, 22, 245), outline=(212, 175, 55, 255), width=4)
    d_emb.ellipse([8, 8, circle_size - 8, circle_size - 8], outline=neon_border, width=3)

    # Logo watermark dentro do emblema
    wm_target = watermark_path or wm_default
    if wm_target and os.path.exists(wm_target):
        try:
            wm = Image.open(wm_target).convert('RGBA')
            wm = wm.resize((circle_size - 22, circle_size - 22), Image.Resampling.LANCZOS)
            emblem_layer.paste(wm, (11, 11), wm)
        except Exception as e:
            print("Watermark error:", e)

    bg.paste(emblem_layer, (ball_x, ball_y), emblem_layer)

    # 8. BADGE SUPERIOR ESQUERDO (Com ponto circular colorido perfeito, sem emoji quebrado)
    d_final = ImageDraw.Draw(bg)
    font_badge = get_font(23)
    text_w = d_final.textlength(badge_label, font=font_badge)
    badge_w = int(text_w + 58)
    badge_h = 42

    # Pílula do badge
    d_final.rounded_rectangle([45, 35, 45 + badge_w, 35 + badge_h], radius=10, fill=badge_bg, outline=(255, 255, 255, 200), width=2)
    # Ponto circular aceso
    d_final.ellipse([58, 48, 72, 62], fill=badge_dot_color, outline=(255, 255, 255, 240), width=1)
    # Texto do badge
    d_final.text((80, 42), badge_label, font=font_badge, fill='white')

    # Moldura fina dourada de acabamento
    d_final.rounded_rectangle([10, 10, 1270, 710], radius=16, outline=(212, 175, 55, 130), width=3)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bg.save(output_path, 'JPEG', quality=95)
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    # Teste 1: Fatos & Debates
    generate_cloud_thumbnail(
        base_frame_path='/tmp/test_clip1_new.jpg',
        output_path='/tmp/cloud_thumb_fatos_v2.jpg',
        title='Toffoli suspende campanha de Renan Santos: sem debates',
        niche='politica'
    )
    # Teste 2: Futebol em Cortes (usando frame puro sem caixa antiga)
    # Vamos extrair um frame puro de videos/clips/2.mp4
    os.system("ffmpeg -y -ss 00:00:02 -i videos/clips/2.mp4 -vframes 1 /tmp/frame_futebol_puro.jpg 2>/dev/null")
    generate_cloud_thumbnail(
        base_frame_path='/tmp/frame_futebol_puro.jpg',
        output_path='/tmp/cloud_thumb_futebol_v2.jpg',
        title='Golaço de Lamine Yamal: camisa 10 resolve',
        niche='futebol'
    )
    # Teste 3: Monetização 3G
    generate_cloud_thumbnail(
        base_frame_path='/tmp/test_clip1_new.jpg',
        output_path='/tmp/cloud_thumb_monetizacao_v2.jpg',
        title='Monetize em 3 dias: Claude Code + YouTube',
        niche='monetizacao',
        badge_text='MONETIZAÇÃO 3G'
    )
