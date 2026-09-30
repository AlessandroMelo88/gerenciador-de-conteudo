"""Compilador de camadas YAML (scripts/compile_prompt_profiles.py)."""
import shutil
import sys
from pathlib import Path

import pytest

pytest.importorskip('yaml')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import compile_prompt_profiles as cpp  # noqa: E402

PROMPTS = ROOT / 'prompts'

CHANNEL = """
channel_id: teste
profile: {slug: teste, name: Teste, niche: teste, niche_aliases: [t], active: true}
targets: [youtube-shorts, youtube-long]
stages:
  selection: {instructions: SEL-CANAL}
  metadata: {instructions: META-CANAL}
  thumbnail: {instructions: THUMB-CANAL}
"""


def _prompts_dir(tmp_path, channel_yaml=CHANNEL):
    d = tmp_path / 'prompts'
    shutil.copytree(PROMPTS / 'layers', d / 'layers')
    shutil.copytree(PROMPTS / 'targets', d / 'targets')
    (d / 'channels').mkdir()
    if channel_yaml is not None:
        (d / 'channels' / 'teste.yaml').write_text(channel_yaml, encoding='utf-8')
    return d


def test_compila_canal_valido_com_as_tres_camadas(tmp_path):
    [p] = cpp.compile_all(_prompts_dir(tmp_path))
    assert p['slug'] == 'teste' and p['niche_aliases'] == ['t'] and p['active'] is True
    assert 'SEL-CANAL' in p['selection_short_prompt'] and 'SEL-CANAL' in p['selection_long_prompt']
    assert 'Short' in p['selection_short_prompt'] and 'segmento horizontal' in p['selection_long_prompt']
    assert 'META-CANAL' in p['metadata_long_prompt']
    assert 'THUMB-CANAL' in p['thumbnail_prompt']


def test_yaml_invalido_da_erro_claro(tmp_path):
    with pytest.raises(cpp.ProfileError, match='YAML inválido'):
        cpp.compile_all(_prompts_dir(tmp_path, 'channel_id: [quebrado\n'))


def test_canal_sem_alvo_longo_e_rejeitado(tmp_path):
    d = _prompts_dir(tmp_path, CHANNEL.replace('[youtube-shorts, youtube-long]', '[youtube-shorts]'))
    with pytest.raises(cpp.ProfileError):
        cpp.compile_all(d)


def test_sem_canais_nao_gera_nada(tmp_path):
    with pytest.raises(cpp.ProfileError, match='Nenhum arquivo de canal'):
        cpp.compile_all(_prompts_dir(tmp_path, None))


def test_camadas_genericas_do_repo_sao_yaml_validos():
    assert cpp.load_yaml(PROMPTS / 'layers' / 'general.yaml')['id'] == 'general'
    assert set(cpp.load_targets(PROMPTS / 'targets')) == {'youtube-shorts', 'youtube-long'}
