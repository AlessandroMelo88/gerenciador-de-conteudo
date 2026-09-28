import os
import sys
import subprocess
import shutil

sys.path.insert(0, os.path.abspath('clip-processor'))
from src.video_processor import _apply_youtube_thumbnail_graphics

os.makedirs('videos/thumbnails', exist_ok=True)

# 1. Clip 1: Toffoli suspende campanha (Fatos & Debates)
if os.path.exists('videos/clips/1.mp4'):
    subprocess.run(['ffmpeg', '-y', '-ss', '00:00:04', '-i', 'videos/clips/1.mp4', '-vframes', '1', '-q:v', '2', 'videos/thumbnails/1.jpg'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
_apply_youtube_thumbnail_graphics('videos/thumbnails/1.jpg', 'TOFFOLI SUSPENDE CAMPANHA: DECISÃO URGENTE NO STF!', niche='politica')

# 2. Clip 2: Futebol em Cortes (Lamine Yamal)
if os.path.exists('videos/thumbnails/736.jpg'):
    shutil.copyfile('videos/thumbnails/736.jpg', 'videos/thumbnails/2.jpg')
_apply_youtube_thumbnail_graphics('videos/thumbnails/2.jpg', 'GOLAÇO DE LAMINE YAMAL! O CAMISA 10 RESOLVE!', niche='futebol')

# 3. Clip 3: Fatos & Debates (Cury)
if os.path.exists('/tmp/raw_frame_1.jpg'):
    shutil.copyfile('/tmp/raw_frame_1.jpg', 'videos/thumbnails/3.jpg')
_apply_youtube_thumbnail_graphics('videos/thumbnails/3.jpg', 'CURY SOBE 9 PONTOS: EMBARALHA ELEIÇÃO!', niche='politica')

# 4. Clip 104: Fatos & Debates no frame 874
if os.path.exists('videos/thumbnails/874.jpg'):
    shutil.copyfile('videos/thumbnails/874.jpg', 'videos/thumbnails/104.jpg')
_apply_youtube_thumbnail_graphics('videos/thumbnails/104.jpg', 'DEBATE ACALORADO AO VIVO: CLIMA ESQUENTA NO ESTÚDIO!', niche='politica')

# 5. Clip 106: Futebol no frame 736
if os.path.exists('videos/thumbnails/736.jpg'):
    shutil.copyfile('videos/thumbnails/736.jpg', 'videos/thumbnails/106.jpg')
_apply_youtube_thumbnail_graphics('videos/thumbnails/106.jpg', 'YURI ALBERTO SALVA O CORINTHIANS: GOLAÇO HISTÓRICO!', niche='futebol')

print("Todas as capas de demonstração atualizadas com sucesso com o novo estilo alinhado!")
