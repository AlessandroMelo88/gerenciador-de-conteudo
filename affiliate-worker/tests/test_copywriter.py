import json
from types import SimpleNamespace

import pytest

from affiliate_worker import copywriter
from tests.conftest import make_offer

GOOD = {'cta_text': 'Conhecer o curso', 'copy_short': 'Curso de oratória para falar em público.',
        'copy_long': 'Parágrafo um.\n\nParágrafo dois.'}


class FakeAnthropic:
    def __init__(self, text=None, exc=None):
        self.text, self.exc, self.kwargs = text, exc, None
        self.messages = self

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.exc:
            raise self.exc
        return SimpleNamespace(content=[SimpleNamespace(type='text', text=self.text)])


class FakeGroq:
    def __init__(self, text=None, exc=None):
        self.text, self.exc, self.kwargs = text, exc, None
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.exc:
            raise self.exc
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.text))])


def test_anthropic_ok():
    a = FakeAnthropic(json.dumps(GOOD))
    g = FakeGroq(exc=AssertionError('não devia chamar'))
    data, used = copywriter.generate_copy(make_offer(), anthropic_client=a, groq_client=g)
    assert used == 'anthropic' and data == GOOD
    assert a.kwargs['model'] == 'claude-haiku-4-5'
    assert 'partidário' in a.kwargs['system']


def test_anthropic_excecao_cai_para_groq():
    a = FakeAnthropic(exc=RuntimeError('sem crédito'))
    g = FakeGroq('```json\n' + json.dumps(GOOD) + '\n```')
    data, used = copywriter.generate_copy(make_offer(), anthropic_client=a, groq_client=g)
    assert used == 'groq' and data['cta_text'] == GOOD['cta_text']
    assert g.kwargs['model'] == copywriter.DEFAULT_GROQ_MODEL


def test_groq_model_do_env(monkeypatch):
    monkeypatch.setenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    g = FakeGroq(json.dumps(GOOD))
    copywriter.generate_copy(make_offer(), provider='groq', groq_client=g)
    assert g.kwargs['model'] == 'llama-3.3-70b-versatile'


def test_json_invalido_nas_duas_cai_para_template():
    a = FakeAnthropic('não é json')
    g = FakeGroq('{"cta_text": "x"}')  # incompleto
    data, used = copywriter.generate_copy(make_offer(niche='futebol', title='Chuteira X'),
                                          anthropic_client=a, groq_client=g)
    assert used == 'template'
    assert set(data) == {'cta_text', 'copy_short', 'copy_long'}
    assert 'Chuteira X' in data['copy_short']


def test_sem_chaves_vai_para_template():
    data, used = copywriter.generate_copy(make_offer())
    assert used == 'template' and data['copy_long']


def test_provider_template_nao_chama_ia():
    a = FakeAnthropic(exc=AssertionError('não devia chamar'))
    _, used = copywriter.generate_copy(make_offer(), provider='template', anthropic_client=a)
    assert used == 'template'


def test_provider_invalido():
    with pytest.raises(ValueError):
        copywriter.generate_copy(make_offer(), provider='openai')


def test_normalizacao_remove_link_e_limita_280():
    raw = {'cta_text': 'Compre', 'copy_short': 'Veja https://evil.example/x ' + 'a ' * 200, 'copy_long': 'ok'}
    data = copywriter.normalize_copy(raw)
    assert 'http' not in data['copy_short'] and len(data['copy_short']) <= 280


def test_parse_com_think_e_texto_em_volta():
    text = '<think>pensando</think>Aqui: ' + json.dumps(GOOD) + ' fim'
    assert copywriter.parse_json_output(text) == GOOD


def test_template_nao_inventa_preco():
    data = copywriter.generate_via_template(make_offer(price_cents=None))
    assert 'R$' not in data['copy_short'] + data['copy_long']
    data = copywriter.generate_via_template(make_offer(price_cents=129990))
    assert 'R$ 1.299,90' in data['copy_short']


def test_apply_copy_preserva_campos_do_operador_e_ignora_sem_link():
    offer = make_offer(cta_text='Meu CTA')
    used = copywriter.apply_copy(offer, provider='template')
    assert used == 'template' and offer.cta_text == 'Meu CTA'
    assert offer.copy_short and offer.ai_provider == 'manual'
    sem_link = make_offer(affiliate_url=None)
    assert copywriter.apply_copy(sem_link, provider='template') is None
    assert sem_link.copy_short is None
