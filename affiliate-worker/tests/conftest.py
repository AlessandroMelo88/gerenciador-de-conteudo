import pytest

from affiliate_worker.models import Offer


class FakeResponse:
    def __init__(self, status_code=200, body=None, headers=None, text=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}
        self.text = text

    def json(self):
        if self._body is None:
            raise ValueError('sem json')
        return self._body


class FakeSession:
    """Session que devolve respostas em sequência (ou exceções) e grava as chamadas."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self, **kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        if callable(item):
            return item(**kwargs)
        return item

    def post(self, url, **kwargs):
        return self._next(url=url, **kwargs)

    def get(self, url, **kwargs):
        return self._next(url=url, **kwargs)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch, tmp_path):
    for var in ('ANTHROPIC_API_KEY', 'GROQ_API_KEY', 'GROQ_MODEL', 'AFFILIATE_API_URL',
                'AFFILIATE_API_TOKEN', 'MERCADOLIVRE_ACCESS_TOKEN'):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv('AFFILIATE_DATA_DIR', str(tmp_path / 'data'))


def make_offer(**overrides) -> Offer:
    base = dict(network='hotmart', external_id='HP1', niche='politica', title='Curso de Oratória',
                affiliate_url='https://go.hotmart.com/X123')
    base.update(overrides)
    return Offer(**base)
