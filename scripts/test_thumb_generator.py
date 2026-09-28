import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def generate_custom_thumbnail(
    base_frame_path: str,
    output_path: str,
    title: str,
    niche: str = 'politica',
    watermark_path: str = 'branding/watermark-fatos-e-debates.png'
):
    # 1. Base 1280x720
    if os.path.exists(base_frame_path):
        bg = Image.open(base_frame_path).convert('RGB')
        bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)
    else:
        bg = Image.new('RGB', (1280, 720), (12, 18, 32))
    
    # Tratamento de contraste e saturação
    bg = ImageEnhance.Contrast(bg).enhance(1.25)
    bg = ImageEnhance.Color(bg).enhance(1.20)
    bg = ImageEnhance.Sharpness(bg).enhance(1.2)
    
    # Vinheta cinematográfica escura nas bordas e na base
    vignette = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    d_v = ImageDraw.Draw(vignette)
    for y in range(300, 720):
        factor = (y - 300) / 420.0
        alpha = int(210 * (factor ** 1.3))
        d_v.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
    for x in range(0, 500):
        factor = 1.0 - (x / 500.0)
        alpha = int(140 * (factor ** 1.4))
        d_v.line([(x, 0), (x, 720)], fill=(0, 0, 0, alpha))
    bg.paste(vignette, (0, 0), vignette)

    # Fontes
    font_bold = None
    for fp in [
        '/System/Library/Fonts/Supplemental/Impact.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/Library/Fonts/Arial Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ]:
        if os.path.exists(fp):
            font_bold = fp
            break

    def get_font(size):
        if font_bold:
            try:
                return ImageFont.truetype(font_bold, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # Processar Texto 1 e Texto 2
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
            text2 = 'DECISÃO URGENTE!'
        else:
            mid = max(2, len(words) // 2)
            text1 = ' '.join(words[:mid]).upper() + '!'
            text2 = ' '.join(words[mid:]).upper()

    if len(text1) > 26:
        text1 = text1[:24] + '...'
    if len(text2) > 30:
        text2 = text2[:28] + '...'

    # 2. Criar a camada do SHADOW BOX em diagonal (-3.5 graus)
    # Criamos em uma imagem transparente maior para poder rotacionar sem serrilhado
    box_w = 1120
    box_h = 220
    box_img = Image.new('RGBA', (box_w, box_h), (0, 0, 0, 0))
    d_box = ImageDraw.Draw(box_img)

    # Caixa com cantos arredondados (fundo preto carvão profundo com leve transparência)
    # Borda dupla: externa ciano/neon e interna dourada
    d_box.rounded_rectangle(
        [10, 10, box_w - 10, box_h - 10],
        radius=20,
        fill=(8, 12, 22, 238),
        outline=(0, 220, 255, 230),
        width=4
    )
    # Linha interna de destaque dourada
    d_box.rounded_rectangle(
        [16, 16, box_w - 16, box_h - 16],
        radius=16,
        outline=(212, 175, 55, 140),
        width=2
    )

    # Texto 1 (Azul / Ciano Elétrico)
    font1 = get_font(60 if len(text1) <= 20 else 52)
    # Função para texto com contorno pesado
    def draw_stroked(d, x, y, text, font, fill_color, stroke_color=(0, 0, 0), stroke_w=6):
        for dx in range(-stroke_w, stroke_w + 1):
            for dy in range(-stroke_w, stroke_w + 1):
                if dx*dx + dy*dy <= stroke_w*stroke_w:
                    d.text((x + dx, y + dy), text, font=font, fill=stroke_color)
        d.text((x, y), text, font=font, fill=fill_color)

    # Desenhar Texto 1 (Azul neon vibrante)
    draw_stroked(d_box, 45, 30, text1, font1, fill_color=(0, 225, 255), stroke_color=(0, 0, 0), stroke_w=6)

    # Desenhar Texto 2 (Branco puro em cima do box shadow)
    font2 = get_font(48 if len(text2) <= 24 else 40)
    draw_stroked(d_box, 45, 115, text2, font2, fill_color=(255, 255, 255), stroke_color=(0, 0, 0), stroke_w=6)

    # 3. Desenhar a "Bola com Efeito" no lado direito do quadrado (conforme o desenho do usuário!)
    circle_size = 170
    cx = box_w - 190
    cy = 25
    # Glow / Aura circular
    glow = Image.new('RGBA', (circle_size + 40, circle_size + 40), (0, 0, 0, 0))
    d_g = ImageDraw.Draw(glow)
    d_g.ellipse([10, 10, circle_size + 30, circle_size + 30], fill=(0, 220, 255, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=12))
    box_img.paste(glow, (cx - 20, cy - 20), glow)

    # Círculo base escuro com anéis dourados e ciano
    d_box.ellipse([cx, cy, cx + circle_size, cy + circle_size], fill=(12, 16, 28, 255), outline=(212, 175, 55, 255), width=5)
    d_box.ellipse([cx + 6, cy + 6, cx + circle_size - 6, cy + circle_size - 6], outline=(0, 220, 255, 200), width=3)

    # Inserir Logo / Brasão oficial dentro do círculo
    if os.path.exists(watermark_path):
        wm = Image.open(watermark_path).convert('RGBA')
        wm = wm.resize((circle_size - 24, circle_size - 24), Image.Resampling.LANCZOS)
        box_img.paste(wm, (cx + 12, cy + 12), wm)

    # 4. Criar a sombra projetada (Drop Shadow do Box)
    # Expandir e aplicar GaussianBlur na silhueta
    shadow = Image.new('RGBA', (box_w + 60, box_h + 60), (0, 0, 0, 0))
    d_sh = ImageDraw.Draw(shadow)
    d_sh.rounded_rectangle([30, 30, box_w + 30, box_h + 30], radius=24, fill=(0, 0, 0, 220))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))

    # 5. Rotacionar a sombra e a caixa com leve inclinação diagonal para cima (-3.5 graus)
    angle = -3.5 # Diagonal para cima
    rotated_shadow = shadow.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    rotated_box = box_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)

    # Posição na thumbnail (parte inferior/central)
    pos_x = 60
    pos_y = 440

    bg.paste(rotated_shadow, (pos_x - 10, pos_y + 15), rotated_shadow)
    bg.paste(rotated_box, (pos_x, pos_y), rotated_box)

    # 6. Badge Superior Esquerdo (🔴 DEBATE AO VIVO ou FATOS & DEBATES)
    d_final = ImageDraw.Draw(bg)
    font_badge = get_font(22)
    badge_label = '🔴 FATOS & DEBATES'
    b_w = d_final.textlength(badge_label, font=font_badge) + 36
    d_final.rounded_rectangle([48, 38, 48 + b_w, 38 + 42], radius=10, fill=(229, 9, 20, 240), outline=(255, 255, 255, 180), width=2)
    d_final.text((66, 45), badge_label, font=font_badge, fill='white')

    # Borda geral fina de acabamento no vídeo (estilo YouTube HD)
    d_final.rounded_rectangle([12, 12, 1268, 708], radius=16, outline=(212, 175, 55, 160), width=3)

    bg.save(output_path, 'JPEG', quality=95)
    print('Thumbnail gerada com sucesso em:', output_path)

if __name__ == '__main__':
    generate_custom_thumbnail(
        base_frame_path='videos/thumbnails/1.jpg',
        output_path='videos/thumbnails/1.jpg',
        title='Toffoli suspende campanha de Renan Santos: sem debates',
        niche='politica'
    )
