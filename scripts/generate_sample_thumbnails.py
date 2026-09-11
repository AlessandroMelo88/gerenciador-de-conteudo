"""
scripts/generate_sample_thumbnails.py — Gera amostras de thumbnails profissionais
estilo MBL / Brigadeiro e GE TV para validação visual antes do deploy.
"""
import os
import sys
from pathlib import Path
import subprocess

# Add clip-processor to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / 'clip-processor'))

from src.video_processor import _apply_youtube_thumbnail_graphics

OUTPUT_DIR = BASE_DIR / 'branding' / 'samples'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    {
        'id': 'politica_sample_1',
        'video': str(BASE_DIR / 'videos' / 'Ui37t_iRlRE.mp4'),
        'at_seconds': 45.0,
        'title': 'MIMIMI DE AR-CONDICIONADO! VEJA O QUE ELE DISSE',
        'niche': 'politica',
    },
    {
        'id': 'politica_sample_2',
        'video': str(BASE_DIR / 'videos' / 'R_3ohi016AA.mp4'),
        'at_seconds': 120.0,
        'title': 'PERDEU A LINHA AO VIVO! JANTADA HISTÓRICA NO DEBATE',
        'niche': 'politica',
    },
    {
        'id': 'futebol_sample_1',
        'video': str(BASE_DIR / 'videos' / 'Ui37t_iRlRE.mp4'),
        'at_seconds': 15.0,
        'title': 'PALMEIRAS VS GALO: QUEM LEVA ESSA DECISÃO?',
        'niche': 'futebol',
    },
    {
        'id': 'futebol_sample_2',
        'video': str(BASE_DIR / 'videos' / 'R_3ohi016AA.mp4'),
        'at_seconds': 60.0,
        'title': 'CRISE NO INTER! DEMISSÃO OU CONTINUIDADE?',
        'niche': 'futebol',
    },
]


def extract_frame(video_path: str, out_path: str, at_sec: float):
    subprocess.run(
        [
            'ffmpeg',
            '-ss', str(at_sec),
            '-i', video_path,
            '-frames:v', '1',
            '-q:v', '2',
            out_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )


def main():
    print('==> Gerando amostras de thumbnails com o novo layout...')
    for s in SAMPLES:
        out_jpg = str(OUTPUT_DIR / f"{s['id']}.jpg")
        print(f"Processando {s['id']} a partir de {s['video']}...")
        if os.path.exists(s['video']):
            extract_frame(s['video'], out_jpg, s['at_seconds'])
        else:
            from PIL import Image
            Image.new('RGB', (1280, 720), color=(20, 24, 33)).save(out_jpg)

        _apply_youtube_thumbnail_graphics(
            thumbnail_path=out_jpg,
            title=s['title'],
            niche=s['niche'],
        )
        print(f"  -> Gerado com sucesso: {out_jpg}")

    print('==> Todas as amostras foram geradas com sucesso em branding/samples/')


if __name__ == '__main__':
    main()
