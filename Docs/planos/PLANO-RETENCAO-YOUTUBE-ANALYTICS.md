# Plano — retenção do YouTube Analytics por clip (SPEC-001, etapa 1 de 3)

> **Para quem executa:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development`
> (recomendada) ou `superpowers:executing-plans` para implementar tarefa a tarefa. Os passos usam
> caixa (`- [ ]`) para acompanhamento.

**Status:** APROVADO, não iniciado (02/10/2026)

**Objetivo:** gravar no banco a retenção real (`averageViewPercentage`) de cada clip publicado, para
que as etapas 2 e 3 possam transformar isso em hipótese aprovada e, daí, em prompt do seletor.

**Arquitetura:** um coletor novo no clip-processor (`retention_collector.py`), irmão do
`metrics_collector.py`, que lê a YouTube Analytics API v2 com o mesmo token OAuth por canal-destino
que o `YouTubeUploader` já carrega, e grava em `clip_daily_metrics` (grão clip × dia, upsert). O
painel só lê a tabela. Nada no painel fala com o Google.

**Stack:** Python 3.11, `google-api-python-client`, APScheduler, psycopg2/pymysql, pytest (pipeline);
Laravel 12, Inertia, React 19, Pest (painel); PostgreSQL 17.

**Spec:** [`../specs/001-retencao-youtube-analytics.md`](../specs/001-retencao-youtube-analytics.md)

## Restrições globais

- **Nenhuma exceção do coletor pode propagar.** Falha de API, de rede ou de banco é logada e o ciclo
  segue. Melhoria de qualidade jamais vira indisponibilidade (regra do projeto; SPEC R7).
- **SQL portável entre PostgreSQL e MySQL.** `db.py` suporta os dois (psycopg2 e pymysql). Nada de
  `ON CONFLICT` nem `ON DUPLICATE KEY`: o upsert é `UPDATE` e, se não afetou linha, `INSERT`.
- **Placeholder de SQL é sempre `%s`**, em ambos os drivers. Cursor devolve dict (`RealDictCursor` /
  `DictCursor`).
- **Migration sempre guardada** por `Schema::hasTable` / `Schema::hasColumn` — em produção as tabelas
  já existem (ADR-0005).
- **Editar código do clip-processor exige rebuild:** não há bind mount para `src/`.
  `docker compose build clip-processor && docker compose up -d clip-processor`.
- **Variável de ambiente nova precisa entrar no `environment:` do `clip-processor`** em
  `canaldecortes/docker-compose.yml`, senão não chega ao container (armadilha de 01/10/2026).
  **Atenção:** existem DOIS composes. O de `canaldecortes/` (Postgres 17, embedder, redis) é o que
  vale e é o espelho da produção; o de `wordpress/` é o compartilhado com os outros projetos e tem
  um `clip-processor` legado ainda apontando para MySQL. Mexer **só** no de `canaldecortes/`.
  No Mac os dois disputam `container_name: postgres`, e o que roda é o compartilhado, com as bases
  de todos os projetos: **não subir** o compose de `canaldecortes/` localmente.
- **Gitflow:** o trabalho inteiro vive em `feature/retencao-youtube-analytics`, que já existe e já tem
  a spec commitada. Commits convencionais em português.
- **Mexer apenas** no serviço `clip-processor` e em paths sob `canaldecortes/`. O `docker-compose.yml`
  da raiz `wordpress/` é compartilhado com kelnab, feeb, placebeads, riodelux e gringo — não tocar.

## Foco de revisão

Casos que a spec implica, que mordem o usuário e que **cada um já tem teste atribuído** na tarefa dona:

1. **Token sem o escopo novo** (estado real de produção até o dono re-autorizar): a chamada tem que
   falhar sozinha e deixar o pipeline publicando. — Tarefa 5.
2. **`columnHeaders` em ordem diferente da pedida**: a API não garante ordem; ler por posição grava
   retenção na coluna de views. — Tarefa 3.
3. **Mesmo dia coletado duas vezes** (o YouTube revisa o dado depois de fechar o dia): tem que
   atualizar, nunca duplicar nem estourar índice único. — Tarefa 4.
4. **Clip sem audiência no dia**: a API simplesmente não devolve linha. Gravar zero mentiria sobre a
   medição; a ausência tem que continuar ausência. — Tarefa 5.
5. **Painel sem nenhum dado de retenção** (antes do backfill): a tela não pode quebrar nem mostrar 0%
   como se fosse medido. — Tarefas 8 e 9.

---

### Tarefa 1: tabela `clip_daily_metrics`

**Arquivos:**
- Criar: `painel/database/migrations/2026_10_02_100000_create_clip_daily_metrics_table.php`
- Teste: `painel/tests/Feature/ClipDailyMetricsSchemaTest.php`

**Interfaces:**
- Consome: nada.
- Produz: a tabela `clip_daily_metrics` com as colunas `generated_clip_id`, `date`, `views`,
  `estimated_minutes_watched`, `average_view_duration`, `average_view_percentage`, `likes`,
  `comments`, `shares`, `subscribers_gained`. Todas as tarefas seguintes usam esses nomes exatos.

- [ ] **Passo 1: escrever o teste que falha**

```php
<?php

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

it('cria clip_daily_metrics com as colunas do contrato', function () {
    expect(Schema::hasTable('clip_daily_metrics'))->toBeTrue();

    foreach ([
        'generated_clip_id', 'date', 'views', 'estimated_minutes_watched',
        'average_view_duration', 'average_view_percentage', 'likes', 'comments',
        'shares', 'subscribers_gained',
    ] as $coluna) {
        expect(Schema::hasColumn('clip_daily_metrics', $coluna))->toBeTrue("falta a coluna {$coluna}");
    }
});

it('recusa duas linhas para o mesmo clip no mesmo dia', function () {
    $clipId = DB::table('generated_clips')->insertGetId([
        'source_video_id' => DB::table('source_videos')->insertGetId([
            'video_id' => 'vid-teste', 'title' => 'fonte', 'status' => 'published',
        ]),
        'title' => 'clip de teste', 'status' => 'published',
    ]);

    $linha = [
        'generated_clip_id' => $clipId, 'date' => '2026-10-01', 'views' => 10,
        'estimated_minutes_watched' => 5, 'average_view_duration' => 30,
        'average_view_percentage' => 42.50,
    ];

    DB::table('clip_daily_metrics')->insert($linha);

    expect(fn () => DB::table('clip_daily_metrics')->insert($linha))
        ->toThrow(Illuminate\Database\QueryException::class);
});
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd painel && vendor/bin/pest tests/Feature/ClipDailyMetricsSchemaTest.php`
Esperado: FALHA — a tabela não existe.

- [ ] **Passo 3: escrever a migration**

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Retenção diária dos clips publicados (SPEC-001, etapa 1).
 *
 * Grão clip × dia, diferente da `clip_metrics`: aquela é snapshot append-only do contador
 * cumulativo; esta é o relatório da YouTube Analytics API por dia, e o YouTube REVISA o dado
 * de um dia depois de fechá-lo — por isso o único em (generated_clip_id, date) e o upsert.
 *
 * `average_view_percentage` é a nota de retenção que as etapas 2 e 3 consomem.
 *
 * FK com ON DELETE CASCADE pelo mesmo motivo da `clip_metrics`: medição é filho descartável e
 * apagar um clip nunca pode falhar por causa dela.
 */
return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('clip_daily_metrics')) {
            return;
        }

        Schema::create('clip_daily_metrics', function (Blueprint $table) {
            $table->id();
            $table->foreignId('generated_clip_id')->constrained('generated_clips')->cascadeOnDelete();
            $table->date('date');
            $table->unsignedBigInteger('views')->default(0);
            $table->unsignedBigInteger('estimated_minutes_watched')->default(0);
            $table->unsignedInteger('average_view_duration')->default(0);
            $table->decimal('average_view_percentage', 5, 2)->default(0);
            $table->unsignedBigInteger('likes')->nullable();
            $table->unsignedBigInteger('comments')->nullable();
            $table->unsignedBigInteger('shares')->nullable();
            $table->integer('subscribers_gained')->nullable();

            $table->unique(['generated_clip_id', 'date'], 'clip_daily_metrics_clip_date_uniq');
            $table->index('date', 'clip_daily_metrics_date_idx');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('clip_daily_metrics');
    }
};
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd painel && vendor/bin/pest tests/Feature/ClipDailyMetricsSchemaTest.php`
Esperado: PASSA (2 testes).

- [ ] **Passo 5: commit**

```bash
git add painel/database/migrations/2026_10_02_100000_create_clip_daily_metrics_table.php \
        painel/tests/Feature/ClipDailyMetricsSchemaTest.php
git commit -m "feat(retencao): tabela clip_daily_metrics, grão clip × dia com único"
```

---

### Tarefa 2: escopo `yt-analytics.readonly` no OAuth

**Arquivos:**
- Modificar: `clip-processor/src/youtube_oauth.py:38-41`
- Teste: `clip-processor/tests/test_youtube_oauth_scopes.py` (criar)

**Interfaces:**
- Consome: nada.
- Produz: `youtube_oauth.SCOPES` com três escopos. A tarefa 5 depende de o token novo tê-los.

- [ ] **Passo 1: escrever o teste que falha**

```python
"""O token precisa nascer com o escopo de leitura do Analytics (SPEC-001 R5)."""
from src import youtube_oauth


def test_scopes_incluem_analytics_readonly():
    assert 'https://www.googleapis.com/auth/yt-analytics.readonly' in youtube_oauth.SCOPES


def test_scopes_de_upload_continuam():
    # Tirar um escopo existente invalidaria o token para publicar.
    assert 'https://www.googleapis.com/auth/youtube.upload' in youtube_oauth.SCOPES
    assert 'https://www.googleapis.com/auth/youtube.force-ssl' in youtube_oauth.SCOPES
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd clip-processor && pytest tests/test_youtube_oauth_scopes.py -v`
Esperado: FALHA em `test_scopes_incluem_analytics_readonly`.

- [ ] **Passo 3: acrescentar o escopo**

Em `clip-processor/src/youtube_oauth.py`, a lista `SCOPES` passa a ser:

```python
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    # Leitura da YouTube Analytics API v2 (retenção por clip, SPEC-001). Token antigo, sem este
    # escopo, continua publicando normalmente: só a chamada de Analytics falha, e ela é engolida.
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd clip-processor && pytest tests/test_youtube_oauth_scopes.py -v`
Esperado: PASSA (2 testes).

- [ ] **Passo 5: commit**

```bash
git add clip-processor/src/youtube_oauth.py clip-processor/tests/test_youtube_oauth_scopes.py
git commit -m "feat(retencao): pede yt-analytics.readonly ao gerar token OAuth"
```

---

### Tarefa 3: ler a resposta da Analytics API por `columnHeaders`

**Arquivos:**
- Criar: `clip-processor/src/retention_collector.py`
- Criar: `clip-processor/tests/test_retention_collector.py`

**Interfaces:**
- Consome: nada.
- Produz:
  - `COLUNAS: dict[str, str]` — de-para do nome da API para o nome da coluna do banco.
  - `parse_report(response: dict) -> list[dict]` — devolve uma lista de dicts com as chaves
    `youtube_video_id`, `date`, `views`, `estimated_minutes_watched`, `average_view_duration`,
    `average_view_percentage`, `likes`, `comments`, `shares`, `subscribers_gained`.
  - `METRICAS: list[str]` e `collector_enabled() -> bool`.

- [ ] **Passo 1: escrever o teste que falha**

```python
"""Retenção: leitura da Analytics API, upsert, janela, cota e escopo (SPEC-001)."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src import retention_collector as rc

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def _resposta(linhas, ordem=None):
    """Resposta da API no formato columnHeaders + rows."""
    ordem = ordem or ['video', 'day', 'views', 'estimatedMinutesWatched', 'averageViewDuration',
                      'averageViewPercentage', 'likes', 'comments', 'shares', 'subscribersGained']
    return {
        'columnHeaders': [{'name': nome} for nome in ordem],
        'rows': [[linha[nome] for nome in ordem] for linha in linhas],
    }


def test_parse_report_mapeia_colunas():
    resposta = _resposta([{
        'video': 'abc123', 'day': '2026-10-01', 'views': 120, 'estimatedMinutesWatched': 40,
        'averageViewDuration': 31, 'averageViewPercentage': 62.5, 'likes': 9, 'comments': 2,
        'shares': 1, 'subscribersGained': 3,
    }])

    linhas = rc.parse_report(resposta)

    assert linhas == [{
        'youtube_video_id': 'abc123', 'date': '2026-10-01', 'views': 120,
        'estimated_minutes_watched': 40, 'average_view_duration': 31,
        'average_view_percentage': 62.5, 'likes': 9, 'comments': 2, 'shares': 1,
        'subscribers_gained': 3,
    }]


def test_parse_report_respeita_ordem_diferente_da_pedida():
    """A API não garante a ordem das colunas; ler por posição gravaria retenção em views."""
    ordem = ['day', 'averageViewPercentage', 'video', 'views', 'estimatedMinutesWatched',
             'averageViewDuration', 'likes', 'comments', 'shares', 'subscribersGained']
    resposta = _resposta([{
        'video': 'xyz', 'day': '2026-10-01', 'views': 10, 'estimatedMinutesWatched': 1,
        'averageViewDuration': 5, 'averageViewPercentage': 88.0, 'likes': 0, 'comments': 0,
        'shares': 0, 'subscribersGained': 0,
    }], ordem=ordem)

    linha = rc.parse_report(resposta)[0]

    assert linha['youtube_video_id'] == 'xyz'
    assert linha['average_view_percentage'] == 88.0
    assert linha['views'] == 10


def test_parse_report_ignora_coluna_desconhecida():
    resposta = {
        'columnHeaders': [{'name': 'video'}, {'name': 'day'}, {'name': 'metricaNova'}],
        'rows': [['abc', '2026-10-01', 7]],
    }

    linha = rc.parse_report(resposta)[0]

    assert linha['youtube_video_id'] == 'abc'
    assert 'metricaNova' not in linha


def test_parse_report_sem_rows_devolve_lista_vazia():
    assert rc.parse_report({'columnHeaders': [], 'rows': []}) == []
    assert rc.parse_report({}) == []
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v`
Esperado: FALHA com `ModuleNotFoundError: No module named 'src.retention_collector'`.

- [ ] **Passo 3: escrever o mínimo**

```python
"""
retention_collector.py — retenção diária dos clips publicados (YouTube Analytics API v2).

Irmão do ``metrics_collector.py``, com a mesma regra de ouro: NENHUMA exceção propaga. O que
falha é logado e o ciclo segue; uma melhoria de qualidade jamais pode virar indisponibilidade.

Diferença para o ``metrics_collector``: lá o grão é snapshot do contador cumulativo
(``videos.list`` part=statistics, append-only); aqui é relatório POR DIA
(``reports.query``, upsert). O YouTube revisa o número de um dia depois de fechá-lo, então a
última leitura daquele dia é a que vale.

``average_view_percentage`` é a nota de retenção: a única métrica que mede o que o selector de
fato decide — se o TRECHO escolhido é bom (SPEC-001).

Credenciais: o mesmo token OAuth por canal-destino do ``YouTubeUploader``
(``/app/youtube/token-{slug}.json``). Exige o escopo ``yt-analytics.readonly``; token antigo sem
ele falha só aqui, e a publicação segue intacta.
"""
import os
from datetime import datetime, timezone

# Métricas pedidas à API. A ordem aqui é só o que se PEDE: a leitura é sempre por columnHeaders.
METRICAS = [
    'views',
    'estimatedMinutesWatched',
    'averageViewDuration',
    'averageViewPercentage',
    'likes',
    'comments',
    'shares',
    'subscribersGained',
]

# De-para entre o nome da coluna da API e a coluna de `clip_daily_metrics`.
COLUNAS = {
    'video': 'youtube_video_id',
    'day': 'date',
    'views': 'views',
    'estimatedMinutesWatched': 'estimated_minutes_watched',
    'averageViewDuration': 'average_view_duration',
    'averageViewPercentage': 'average_view_percentage',
    'likes': 'likes',
    'comments': 'comments',
    'shares': 'shares',
    'subscribersGained': 'subscribers_gained',
}


def collector_enabled() -> bool:
    """RETENTION_COLLECTOR_ENABLED (default ligado) desliga o job sem mexer no resto."""
    return os.environ.get('RETENTION_COLLECTOR_ENABLED', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [RETENCAO] {msg}', flush=True)


def parse_report(response: dict) -> list[dict]:
    """Normaliza a resposta de reports.query nas chaves de `clip_daily_metrics`.

    Lê SEMPRE por `columnHeaders`: a API não garante devolver as colunas na ordem pedida, e ler
    por posição gravaria retenção na coluna de views.
    """
    response = response or {}
    cabecalhos = [c.get('name') for c in response.get('columnHeaders') or []]
    linhas = []
    for row in response.get('rows') or []:
        linha = {}
        for nome, valor in zip(cabecalhos, row):
            coluna = COLUNAS.get(nome)
            if coluna is not None:
                linha[coluna] = valor
        linhas.append(linha)
    return linhas
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v`
Esperado: PASSA (4 testes).

- [ ] **Passo 5: commit**

```bash
git add clip-processor/src/retention_collector.py clip-processor/tests/test_retention_collector.py
git commit -m "feat(retencao): lê o relatório do Analytics por columnHeaders"
```

---

### Tarefa 4: upsert portável de `clip_daily_metrics`

**Arquivos:**
- Modificar: `clip-processor/src/retention_collector.py`
- Modificar: `clip-processor/tests/test_retention_collector.py`

**Interfaces:**
- Consome: `parse_report` e `COLUNAS` da tarefa 3.
- Produz: `upsert_linhas(conn, por_clip: dict[str, int], linhas: list[dict]) -> int`, onde
  `por_clip` mapeia `youtube_video_id` para `generated_clips.id`. Devolve quantas linhas gravou.

- [ ] **Passo 1: escrever o teste que falha**

```python
def test_upsert_atualiza_quando_o_dia_ja_existe():
    """O YouTube revisa o dado de um dia; coletar de novo atualiza, nunca duplica."""
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.rowcount = 1  # o UPDATE achou a linha

    gravadas = rc.upsert_linhas(conn, {'abc': 7}, [{
        'youtube_video_id': 'abc', 'date': '2026-10-01', 'views': 120,
        'estimated_minutes_watched': 40, 'average_view_duration': 31,
        'average_view_percentage': 62.5,
    }])

    assert gravadas == 1
    sqls = [c.args[0] for c in cur.execute.call_args_list]
    assert any(sql.startswith('UPDATE clip_daily_metrics') for sql in sqls)
    assert not any(sql.startswith('INSERT INTO clip_daily_metrics') for sql in sqls)


def test_upsert_insere_quando_o_dia_e_novo():
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.rowcount = 0  # o UPDATE não achou nada

    gravadas = rc.upsert_linhas(conn, {'abc': 7}, [{
        'youtube_video_id': 'abc', 'date': '2026-10-01', 'views': 120,
        'estimated_minutes_watched': 40, 'average_view_duration': 31,
        'average_view_percentage': 62.5,
    }])

    assert gravadas == 1
    sqls = [c.args[0] for c in cur.execute.call_args_list]
    assert any(sql.startswith('INSERT INTO clip_daily_metrics') for sql in sqls)


def test_upsert_ignora_video_que_nao_e_de_clip_conhecido():
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value

    gravadas = rc.upsert_linhas(conn, {'abc': 7}, [{'youtube_video_id': 'outro', 'date': '2026-10-01'}])

    assert gravadas == 0
    assert cur.execute.call_count == 0


def test_upsert_nao_usa_sintaxe_de_um_banco_so():
    """db.py fala PostgreSQL e MySQL: ON CONFLICT / ON DUPLICATE KEY quebrariam em um dos dois."""
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.rowcount = 0

    rc.upsert_linhas(conn, {'abc': 7}, [{
        'youtube_video_id': 'abc', 'date': '2026-10-01', 'views': 1,
        'estimated_minutes_watched': 1, 'average_view_duration': 1,
        'average_view_percentage': 1.0,
    }])

    sqls = ' '.join(c.args[0] for c in cur.execute.call_args_list).upper()
    assert 'ON CONFLICT' not in sqls
    assert 'ON DUPLICATE KEY' not in sqls
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v -k upsert`
Esperado: FALHA com `AttributeError: module 'src.retention_collector' has no attribute 'upsert_linhas'`.

- [ ] **Passo 3: escrever o mínimo**

Acrescentar ao fim de `retention_collector.py`:

```python
# Colunas gravadas, na ordem usada tanto pelo UPDATE quanto pelo INSERT.
_GRAVAVEIS = [
    'views', 'estimated_minutes_watched', 'average_view_duration', 'average_view_percentage',
    'likes', 'comments', 'shares', 'subscribers_gained',
]


def upsert_linhas(conn, por_clip: dict, linhas: list[dict]) -> int:
    """Grava as linhas do relatório, uma por clip por dia.

    Upsert à mão (UPDATE e, se não afetou linha, INSERT) porque `db.py` fala PostgreSQL e MySQL:
    `ON CONFLICT` e `ON DUPLICATE KEY` são de um dialeto só. O volume é pequeno — a janela de
    coleta é de 30 dias — então duas idas ao banco por linha não pesam.
    """
    gravadas = 0
    with conn.cursor() as cur:
        for linha in linhas:
            clip_id = por_clip.get(linha.get('youtube_video_id'))
            if clip_id is None or not linha.get('date'):
                continue
            valores = [linha.get(coluna) for coluna in _GRAVAVEIS]

            sets = ', '.join(f'{coluna} = %s' for coluna in _GRAVAVEIS)
            cur.execute(
                f'UPDATE clip_daily_metrics SET {sets} WHERE generated_clip_id = %s AND date = %s',
                valores + [clip_id, linha['date']],
            )
            if cur.rowcount == 0:
                colunas = ', '.join(['generated_clip_id', 'date'] + _GRAVAVEIS)
                marcas = ', '.join(['%s'] * (len(_GRAVAVEIS) + 2))
                cur.execute(
                    f'INSERT INTO clip_daily_metrics ({colunas}) VALUES ({marcas})',
                    [clip_id, linha['date']] + valores,
                )
            gravadas += 1
    conn.commit()
    return gravadas
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v`
Esperado: PASSA (8 testes).

- [ ] **Passo 5: commit**

```bash
git add clip-processor/src/retention_collector.py clip-processor/tests/test_retention_collector.py
git commit -m "feat(retencao): upsert por clip e dia, portável entre PostgreSQL e MySQL"
```

---

### Tarefa 5: ciclo de coleta — candidatos, cota, escopo e dia sem audiência

**Arquivos:**
- Modificar: `clip-processor/src/retention_collector.py`
- Modificar: `clip-processor/tests/test_retention_collector.py`

**Interfaces:**
- Consome: `parse_report`, `upsert_linhas`, `collector_enabled`, `METRICAS` das tarefas 3 e 4.
- Produz: `run_retention_collection_once(conn=None, now=None, service_for=None, dias=None) -> int`.
  `service_for(slug)` devolve um serviço com `.reports().query(**kw).execute()`. A tarefa 6 agenda
  essa função; a tarefa 7 a reusa com `dias` grande.

- [ ] **Passo 1: escrever o teste que falha**

```python
@pytest.fixture(autouse=True)
def _limpa_estado(monkeypatch):
    rc._calls_today.clear()
    monkeypatch.delenv('RETENTION_COLLECTOR_ENABLED', raising=False)
    monkeypatch.delenv('RETENTION_MAX_CALLS_PER_CHANNEL_DAY', raising=False)


def _clip(i, *, dias=2, slug='canal-a'):
    return {
        'id': i,
        'youtube_video_id': f'vid{i}',
        'published_at': NOW - timedelta(days=dias),
        'channel_slug': slug,
    }


def _conn(rows):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = rows
    cur.rowcount = 0
    return conn


def _service(linhas=None, erro=None):
    """Analytics falso: reports().query(...).execute() devolve columnHeaders + rows."""
    service = MagicMock()
    chamadas = []

    def query(**kw):
        chamadas.append(kw)
        req = MagicMock()
        if erro:
            req.execute.side_effect = erro
        else:
            req.execute.return_value = _resposta(linhas or [])
        return req

    service.reports.return_value.query.side_effect = query
    service.chamadas = chamadas
    return service


def test_ciclo_grava_a_retencao_dos_clips_publicados():
    conn = _conn([_clip(7)])
    service = _service([{
        'video': 'vid7', 'day': '2026-10-01', 'views': 120, 'estimatedMinutesWatched': 40,
        'averageViewDuration': 31, 'averageViewPercentage': 62.5, 'likes': 9, 'comments': 2,
        'shares': 1, 'subscribersGained': 3,
    }])

    gravadas = rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda slug: service)

    assert gravadas == 1
    assert service.chamadas[0]['ids'] == 'channel==MINE'
    assert 'averageViewPercentage' in service.chamadas[0]['metrics']
    assert service.chamadas[0]['dimensions'] == 'video,day'


def test_desligado_por_env_nao_chama_a_api():
    conn = _conn([_clip(7)])
    service = _service()

    import os
    os.environ['RETENTION_COLLECTOR_ENABLED'] = 'false'
    try:
        assert rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service) == 0
    finally:
        del os.environ['RETENTION_COLLECTOR_ENABLED']

    assert service.chamadas == []


def test_token_sem_escopo_de_analytics_nao_derruba_o_ciclo():
    """Estado real de produção até o dono re-autorizar: a chamada falha e o pipeline segue."""
    conn = _conn([_clip(7)])
    service = _service(erro=Exception('insufficientPermissions: Request had insufficient authentication scopes.'))

    gravadas = rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service)

    assert gravadas == 0  # não levantou exceção


def test_credencial_ausente_nao_derruba_o_ciclo():
    conn = _conn([_clip(7)])

    def service_for(slug):
        raise FileNotFoundError('Token OAuth não encontrado')

    assert rc.run_retention_collection_once(conn=conn, now=NOW, service_for=service_for) == 0


def test_dia_sem_audiencia_nao_vira_linha_zerada():
    """A API simplesmente não devolve linha; gravar zero mentiria sobre a medição."""
    conn = _conn([_clip(7)])
    service = _service([])  # resposta sem rows

    assert rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service) == 0
    cur = conn.cursor.return_value.__enter__.return_value
    sqls = ' '.join(str(c.args[0]) for c in cur.execute.call_args_list)
    assert 'INSERT INTO clip_daily_metrics' not in sqls


def test_teto_de_chamadas_por_canal_interrompe_o_canal(monkeypatch):
    monkeypatch.setenv('RETENTION_MAX_CALLS_PER_CHANNEL_DAY', '1')
    conn = _conn([_clip(i) for i in range(1, 120)])  # força mais de um lote
    service = _service([])

    rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service)

    assert len(service.chamadas) == 1


def test_clip_mais_velho_que_a_janela_nao_entra():
    conn = _conn([])  # a consulta já filtra por data; o teste fixa o corte enviado ao banco
    service = _service([])

    rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service)

    cur = conn.cursor.return_value.__enter__.return_value
    corte = cur.execute.call_args_list[0].args[1][-1]
    assert corte == NOW - timedelta(days=rc.STOP_DAYS)
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v -k "ciclo or teto or token or escopo or credencial or audiencia or janela"`
Esperado: FALHA — `run_retention_collection_once` não existe.

- [ ] **Passo 3: escrever o mínimo**

Acrescentar ao `retention_collector.py` (e `from datetime import timedelta` no topo):

```python
BATCH_SIZE = 50          # ids por chamada, como no metrics_collector
STOP_DAYS = 30           # janela de coleta por clip, alinhada ao metrics_collector

_calls_today: dict[tuple[str, str], int] = {}


def _max_calls_per_channel_day() -> int:
    try:
        return int(os.environ.get('RETENTION_MAX_CALLS_PER_CHANNEL_DAY', '200'))
    except ValueError:
        return 200


def _channel_has_budget(slug: str, now: datetime) -> bool:
    return _calls_today.get((slug, now.date().isoformat()), 0) < _max_calls_per_channel_day()


def _count_call(slug: str, now: datetime) -> None:
    key = (slug, now.date().isoformat())
    for old in [k for k in _calls_today if k[1] != key[1]]:
        del _calls_today[old]
    _calls_today[key] = _calls_today.get(key, 0) + 1


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _fetch_candidates(conn, now: datetime, dias: int) -> list[dict]:
    cutoff = now - timedelta(days=dias)
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.youtube_video_id, gc.published_at, dc.slug AS channel_slug '
            'FROM generated_clips gc '
            'LEFT JOIN destination_channels dc ON dc.id = gc.destination_channel_id '
            "WHERE gc.status = 'published' AND gc.youtube_video_id IS NOT NULL "
            'AND gc.youtube_video_id <> %s AND gc.published_at >= %s',
            ('', cutoff),
        )
        return list(cur.fetchall())


def _as_date(value) -> str:
    if isinstance(value, str):
        return value[:10]
    return value.strftime('%Y-%m-%d')


def _collect_channel(conn, slug, clips: list[dict], now: datetime, service_for, dias: int) -> int:
    budget_key = slug or '_legado'
    try:
        service = service_for(slug)
    except Exception as exc:
        _log(f'Canal {budget_key}: sem credencial utilizável ({exc}) — pulando')
        return 0

    inicio = _as_date(min(c['published_at'] for c in clips))
    fim = _as_date(now - timedelta(days=1))  # o dia de hoje ainda não fechou na Analytics
    gravadas = 0

    for lote in _chunks(clips, BATCH_SIZE):
        if not _channel_has_budget(budget_key, now):
            _log(f'Canal {budget_key}: teto diário de chamadas atingido — retoma amanhã')
            break
        por_clip = {c['youtube_video_id']: c['id'] for c in lote}
        try:
            _count_call(budget_key, now)
            resposta = service.reports().query(
                ids='channel==MINE',
                startDate=inicio,
                endDate=fim,
                dimensions='video,day',
                metrics=','.join(METRICAS),
                filters='video==' + ','.join(por_clip),
                maxResults=200,
            ).execute()
        except Exception as exc:
            _log(f'Canal {budget_key}: reports.query falhou ({exc}) — segue sem derrubar o ciclo')
            continue

        linhas = parse_report(resposta)
        if not linhas:
            continue
        try:
            gravadas += upsert_linhas(conn, por_clip, linhas)
        except Exception as exc:
            _log(f'Canal {budget_key}: falha ao gravar retenção ({exc})')
            try:
                conn.rollback()
            except Exception:
                pass
    return gravadas


def _default_service_for(slug):
    """Reusa o token do uploader e abre o serviço de Analytics com as mesmas credenciais."""
    from googleapiclient.discovery import build

    from src.uploader import YouTubeUploader

    uploader = YouTubeUploader(channel_slug=slug) if slug else YouTubeUploader()
    return build('youtubeAnalytics', 'v2', credentials=uploader._load_credentials())


def run_retention_collection_once(conn=None, now=None, service_for=None, dias=None) -> int:
    """Um ciclo de coleta. Nunca levanta exceção. Devolve o nº de linhas gravadas."""
    if not collector_enabled():
        return 0
    now = now or datetime.now(timezone.utc)
    dias = STOP_DAYS if dias is None else dias
    service_for = service_for or _default_service_for
    owns_conn = conn is None
    try:
        if owns_conn:
            from src.db import get_db_connection
            conn = get_db_connection()
        candidatos = [c for c in _fetch_candidates(conn, now, dias) if c.get('youtube_video_id')]
        if not candidatos:
            return 0
        por_canal: dict = {}
        for c in candidatos:
            por_canal.setdefault(c.get('channel_slug'), []).append(c)
        total = 0
        for slug, clips in por_canal.items():
            total += _collect_channel(conn, slug, clips, now, service_for, dias)
        _log(f'Coleta concluída: {total} linha(s) de retenção de {len(candidatos)} clip(s)')
        return total
    except Exception as exc:
        _log(f'Aviso: coleta de retenção falhou — {exc}')
        return 0
    finally:
        if owns_conn and conn is not None:
            try:
                conn.close()
            except Exception:
                pass
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v`
Esperado: PASSA (15 testes).

- [ ] **Passo 5: commit**

```bash
git add clip-processor/src/retention_collector.py clip-processor/tests/test_retention_collector.py
git commit -m "feat(retencao): ciclo diário de coleta com teto de cota e falha contida"
```

---

### Tarefa 6: agendar o job e passar as variáveis ao container

**Arquivos:**
- Modificar: `clip-processor/src/main.py` (import junto da linha 56; `add_job` depois do bloco do
  `metrics_collector`, que hoje termina na linha 296)
- Modificar: `canaldecortes/docker-compose.yml` (serviço `clip-processor`, **só** esse serviço)
- Modificar: `canaldecortes/.env.example` (documentar as duas variáveis novas, sem valor)
- Modificar: `clip-processor/tests/test_retention_collector.py`

**Interfaces:**
- Consome: `run_retention_collection_once` e `collector_enabled` da tarefa 5.
- Produz: job `retention_collector` no scheduler, de 24 em 24 horas.

- [ ] **Passo 1: escrever o teste que falha**

```python
def test_scheduler_agenda_a_coleta_de_retencao_uma_vez_por_dia():
    """A Analytics consolida por dia; coletar de hora em hora só gastaria cota."""
    import src.main as main

    jobs = {j.id: j for j in main.scheduler.get_jobs()}

    assert 'retention_collector' in jobs, 'o job de retenção não foi agendado'
    assert jobs['retention_collector'].trigger.interval == timedelta(hours=24)
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v -k scheduler`
Esperado: FALHA — `'o job de retenção não foi agendado'`.

- [ ] **Passo 3: agendar**

Em `clip-processor/src/main.py`, junto do import do coletor de métricas (linha 56):

```python
from src.retention_collector import collector_enabled as retention_enabled
from src.retention_collector import run_retention_collection_once
```

E logo depois do bloco `if collector_enabled():` do `metrics_collector`:

```python
# Retenção (YouTube Analytics): uma vez por dia, porque a Analytics consolida por dia — coletar de
# hora em hora só gastaria cota. Não depende de PIPELINE_ENABLED (é leitura) e nunca derruba o
# scheduler: o coletor engole os próprios erros. RETENTION_COLLECTOR_ENABLED=false desliga.
if retention_enabled():
    scheduler.add_job(
        run_retention_collection_once,
        'interval',
        hours=24,
        id='retention_collector',
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
```

Em `canaldecortes/docker-compose.yml`, no `environment:` do serviço **`clip-processor`** (e em
nenhum outro; o compose da raiz `wordpress/` não é tocado):

```yaml
      RETENTION_COLLECTOR_ENABLED: ${RETENTION_COLLECTOR_ENABLED:-true}
      RETENTION_MAX_CALLS_PER_CHANNEL_DAY: ${RETENTION_MAX_CALLS_PER_CHANNEL_DAY:-200}
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v`
Esperado: PASSA (16 testes).

Conferir que nenhum outro projeto foi tocado: `git diff docker-compose.yml` deve mostrar apenas
linhas dentro do serviço `clip-processor`.

- [ ] **Passo 5: commit**

```bash
git add clip-processor/src/main.py clip-processor/tests/test_retention_collector.py docker-compose.yml
git commit -m "feat(retencao): agenda a coleta diária e passa as variáveis ao clip-processor"
```

---

### Tarefa 7: comando de carga retroativa

**Arquivos:**
- Criar: `clip-processor/src/retention_backfill.py`
- Modificar: `clip-processor/tests/test_retention_collector.py`

**Interfaces:**
- Consome: `run_retention_collection_once(dias=...)` da tarefa 5.
- Produz: `python -m src.retention_backfill [--dias N]`, padrão 400 dias.

- [ ] **Passo 1: escrever o teste que falha**

```python
def test_backfill_pede_uma_janela_maior_que_a_do_job_diario():
    from src import retention_backfill

    chamadas = {}

    def falso(dias=None, **kw):
        chamadas['dias'] = dias
        return 3

    retention_backfill.main(['--dias', '400'], runner=falso)

    assert chamadas['dias'] == 400
    assert chamadas['dias'] > rc.STOP_DAYS


def test_backfill_usa_400_dias_por_padrao():
    from src import retention_backfill

    chamadas = {}
    retention_backfill.main([], runner=lambda dias=None, **kw: chamadas.setdefault('dias', dias) or 0)

    assert chamadas['dias'] == 400
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v -k backfill`
Esperado: FALHA com `ModuleNotFoundError: No module named 'src.retention_backfill'`.

- [ ] **Passo 3: escrever o mínimo**

```python
"""
retention_backfill.py — carga retroativa da retenção (SPEC-001 R15).

Rodado À MÃO, uma vez, depois que os canais forem re-autorizados com o escopo
`yt-analytics.readonly`. Fica separado do job diário de propósito: carga histórica e operação têm
perfis de cota e de risco diferentes, e misturar as duas esconde qual delas estourou o teto.

    docker compose exec clip-processor python -m src.retention_backfill --dias 400
"""
import argparse
import sys

from src.retention_collector import run_retention_collection_once

DIAS_PADRAO = 400  # cobre o projeto inteiro (primeiro commit em 17/06/2026)


def main(argv=None, runner=run_retention_collection_once) -> int:
    parser = argparse.ArgumentParser(description='Carga retroativa da retenção por clip.')
    parser.add_argument('--dias', type=int, default=DIAS_PADRAO,
                        help=f'quantos dias para trás considerar (padrão: {DIAS_PADRAO})')
    args = parser.parse_args(argv)

    gravadas = runner(dias=args.dias)
    print(f'[RETENCAO] Backfill concluído: {gravadas} linha(s) gravadas em {args.dias} dias.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd clip-processor && pytest tests/test_retention_collector.py -v`
Esperado: PASSA (18 testes).

- [ ] **Passo 5: commit**

```bash
git add clip-processor/src/retention_backfill.py clip-processor/tests/test_retention_collector.py
git commit -m "feat(retencao): comando de carga retroativa, separado do job diário"
```

---

### Tarefa 8: o painel lê a retenção

**Arquivos:**
- Modificar: `painel/app/Services/MetricsReport.php`
- Teste: `painel/tests/Feature/MetricsRetencaoTest.php` (criar)

**Interfaces:**
- Consome: a tabela `clip_daily_metrics` da tarefa 1.
- Produz: no retorno de `MetricsReport::build()`, a chave `hasRetention` (bool) e, em cada linha de
  `bySource`, `byFormat` e `lowViews`, a chave `avgRetention` (float|null) / `retention`
  (float|null). A tarefa 9 consome exatamente esses nomes.

- [ ] **Passo 1: escrever o teste que falha**

```php
<?php

use App\Services\MetricsReport;
use Illuminate\Support\Facades\DB;

function clipPublicado(string $titulo, string $canal, int $diasAtras = 10): int
{
    $canalId = DB::table('source_channels')->insertGetId([
        'channel_name' => $canal, 'channel_id' => 'uc-'.$canal, 'target_niche' => 'futebol',
    ]);
    $videoId = DB::table('source_videos')->insertGetId([
        'video_id' => 'src-'.$titulo, 'title' => 'fonte', 'status' => 'published',
        'channel_id' => $canalId, 'format' => 'curto',
    ]);

    return DB::table('generated_clips')->insertGetId([
        'source_video_id' => $videoId, 'title' => $titulo, 'status' => 'published',
        'youtube_video_id' => 'yt-'.$titulo, 'published_at' => now()->subDays($diasAtras),
    ]);
}

it('ordena os canais-fonte por retenção média quando há dado', function () {
    $fraco = clipPublicado('clip-fraco', 'Canal Fraco');
    $forte = clipPublicado('clip-forte', 'Canal Forte');

    foreach ([[$fraco, 20.0], [$forte, 75.0]] as [$clipId, $retencao]) {
        DB::table('clip_daily_metrics')->insert([
            'generated_clip_id' => $clipId, 'date' => now()->subDays(9)->toDateString(),
            'views' => 100, 'estimated_minutes_watched' => 10, 'average_view_duration' => 20,
            'average_view_percentage' => $retencao,
        ]);
        DB::table('clip_metrics')->insert([
            'generated_clip_id' => $clipId, 'collected_at' => now()->subDays(9), 'views' => 100,
        ]);
    }

    $dados = app(MetricsReport::class)->build();

    expect($dados['hasRetention'])->toBeTrue()
        ->and($dados['bySource'][0]['source'])->toBe('Canal Forte')
        ->and($dados['bySource'][0]['avgRetention'])->toBe(75.0);
});

it('não quebra nem inventa zero quando ainda não há retenção coletada', function () {
    $clipId = clipPublicado('clip-sem-retencao', 'Canal Sem Dado');
    DB::table('clip_metrics')->insert([
        'generated_clip_id' => $clipId, 'collected_at' => now()->subDays(9), 'views' => 100,
    ]);

    $dados = app(MetricsReport::class)->build();

    expect($dados['hasRetention'])->toBeFalse()
        ->and($dados['bySource'][0]['avgRetention'])->toBeNull()
        ->and($dados['bySource'][0]['avgViewsNow'])->toBe(100);
});
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd painel && vendor/bin/pest tests/Feature/MetricsRetencaoTest.php`
Esperado: FALHA — `Undefined array key "hasRetention"`.

- [ ] **Passo 3: implementar**

Em `MetricsReport::build()`, depois do bloco que carrega `$snapshots` e antes do `foreach ($clips ...)`:

```php
        // Retenção por clip: média do `average_view_percentage` dos dias medidos. Ausência de dado
        // continua ausência (null), nunca 0 — zero seria uma medição, e não medimos nada.
        $retention = [];
        foreach ($clips->pluck('id')->chunk(1000) as $ids) {
            DB::table('clip_daily_metrics')
                ->whereIn('generated_clip_id', $ids->all())
                ->get(['generated_clip_id', 'average_view_percentage'])
                ->each(function ($row) use (&$retention) {
                    $retention[$row->generated_clip_id][] = (float) $row->average_view_percentage;
                });
        }
```

Dentro do `foreach ($clips as $clip)`, acrescentar ao array de `$measured[]`:

```php
                'retention' => isset($retention[$clip->id])
                    ? round(array_sum($retention[$clip->id]) / count($retention[$clip->id]), 2)
                    : null,
```

No `return` de `build()`, acrescentar:

```php
            'hasRetention' => array_filter(array_column($measured, 'retention'), fn ($v) => $v !== null) !== [],
```

Acrescentar o helper à classe:

```php
    /** Média de retenção de um grupo; null quando nenhum clip do grupo foi medido. */
    private function avgRetention(array $group): ?float
    {
        $valores = array_values(array_filter(array_column($group, 'retention'), fn ($v) => $v !== null));

        return $valores === [] ? null : round(array_sum($valores) / count($valores), 2);
    }
```

Em `byFormat()` e `bySource()`, acrescentar a cada linha montada:

```php
                'avgRetention' => $this->avgRetention($group),
```

E em `bySource()`, a ordenação passa a privilegiar retenção quando ela existe, caindo para views
quando não existe (sem retenção o relatório segue igual ao de hoje):

```php
        usort($rows, function ($a, $b) {
            if ($a['avgRetention'] !== null || $b['avgRetention'] !== null) {
                return [$b['avgRetention'] ?? -1, $b['clips']] <=> [$a['avgRetention'] ?? -1, $a['clips']];
            }

            return [$b['avgViewsNow'], $b['clips']] <=> [$a['avgViewsNow'], $a['clips']];
        });
```

Em `lowViews()`, acrescentar ao array devolvido por clip:

```php
            'retention' => $c['retention'],
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd painel && vendor/bin/pest tests/Feature/MetricsRetencaoTest.php tests/Feature/MetricsPageTest.php`
Esperado: PASSA, inclusive os testes que já existiam da tela.

- [ ] **Passo 5: commit**

```bash
git add painel/app/Services/MetricsReport.php painel/tests/Feature/MetricsRetencaoTest.php
git commit -m "feat(retencao): painel ordena canais-fonte por retenção, sem inventar zero"
```

---

### Tarefa 9: mostrar a retenção na tela

**Arquivos:**
- Modificar: `painel/resources/js/pages/Metrics.tsx`
- Modificar: `painel/tests/Feature/MetricsPageTest.php`

**Interfaces:**
- Consome: `hasRetention`, `avgRetention` e `retention` da tarefa 8.
- Produz: nada que outra tarefa consuma.

- [ ] **Passo 1: escrever o teste que falha**

```php
it('entrega retenção às props da tela de métricas', function () {
    $this->actingAs(User::first() ?? User::factory()->create())
        ->get('/painel/metricas')
        ->assertInertia(fn ($page) => $page
            ->component('Metrics')
            ->has('hasRetention')
            ->has('bySource.0.avgRetention')
        );
});
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd painel && vendor/bin/pest tests/Feature/MetricsPageTest.php`
Esperado: FALHA se a tarefa 8 não estiver aplicada; se estiver, PASSA já aqui — nesse caso siga para
o passo 3, que é a parte visual, e confirme pelo navegador.

- [ ] **Passo 3: exibir na tela**

Em `painel/resources/js/pages/Metrics.tsx`, nos tipos do topo do arquivo (linhas 9-47), acrescentar
o campo novo a cada linha e às props:

```tsx
type FormatRow = {
    // ...campos que já existem
    avgRetention: number | null;
};

type SourceRow = {
    // ...campos que já existem
    avgRetention: number | null;
};

type LowRow = {
    // ...campos que já existem
    retention: number | null;
};

type PageProps = {
    // ...campos que já existem
    hasRetention: boolean;
};
```

Ao lado de `formatNumber` (linha 51), um formatador que nunca transforma ausência em zero:

```tsx
/** Retenção como percentual. Sem medição é travessão: 0% seria uma medição, e não medimos nada. */
function formatRetention(value: number | null): string {
    return value === null ? '—' : `${value.toFixed(1)}%`;
}
```

Na tabela "Qual canal de origem rende mais", uma coluna nova. No `TableHeader`, logo depois do
`TableHead` de "Clips":

```tsx
                                            <TableHead className="px-5 py-3 font-semibold text-right">Retenção média</TableHead>
```

E no `TableBody`, na mesma posição da linha:

```tsx
                                                <TableCell className="px-5 py-3 text-right font-mono font-semibold">{formatRetention(row.avgRetention)}</TableCell>
```

A `description` daquele `SectionCard` passa a dizer o novo critério de ordem:

```tsx
                            description="De onde saíram os vídeos que viraram clips, do que mais para o que menos segura o espectador (retenção média por clip; sem retenção coletada, ordena por visualizações)."
```

O mesmo par de linhas entra na tabela "Clips que não pegaram", usando `formatRetention(row.retention)`,
e no `FormatCard` (linha 69) como mais uma linha de número, com o rótulo "Retenção média".

Por fim, o aviso de dado ausente, logo antes do `<div className="grid gap-3 ...">` dos cards de
formato (linha 123):

```tsx
                        {!hasRetention && (
                            <p className="rounded-md border border-dashed border-muted-foreground/30 px-4 py-3 text-xs text-muted-foreground">
                                Retenção ainda não coletada. Os canais precisam ser reautorizados no Google
                                com o escopo de Analytics e a carga retroativa precisa rodar uma vez.
                            </p>
                        )}
```

`hasRetention` vem de `usePage<PageProps>().props`, junto dos demais campos já desestruturados.
As tabelas continuam aparecendo com os números de visualizações nesse estado.

- [ ] **Passo 4: conferir**

Rodar: `cd painel && vendor/bin/pest tests/Feature/MetricsPageTest.php && npm run build`
Esperado: testes passam e o build do Vite termina sem erro.

Validação visual: usar a skill `validacao-visual` em `/painel/metricas`, conferindo os dois estados
(com retenção e sem retenção).

- [ ] **Passo 5: commit**

```bash
git add painel/resources/js/pages/Metrics.tsx painel/tests/Feature/MetricsPageTest.php
git commit -m "feat(retencao): coluna de retenção na tela de métricas, com aviso de dado ausente"
```

---

### Tarefa 10: documentação e fechamento

**Arquivos:**
- Modificar: `Docs/specs/001-retencao-youtube-analytics.md` (Status e critérios de pronto)
- Modificar: `Docs/sistema/SISTEMA-CLIP-PROCESSOR.md` (o coletor novo)
- Modificar: `Docs/sistema/BANCO-DE-DADOS.md` (a tabela nova)
- Modificar: `Docs/PROGRESSO.md` e `Docs/ESTADO-DO-PROJETO.md`
- Criar: `CHANGELOG.d/retencao-youtube-analytics.novidade.md`

- [ ] **Passo 1: escrever a documentação**

No `SISTEMA-CLIP-PROCESSOR.md`, uma seção "Coleta de retenção (`retention_collector.py`)": o que
coleta, de onde, com que frequência, as duas variáveis de ambiente, e a diferença para o
`metrics_collector` (snapshot cumulativo × relatório por dia).

No `BANCO-DE-DADOS.md`, a tabela `clip_daily_metrics` com as colunas e o único.

No `ESTADO-DO-PROJETO.md`, §6 "Em aberto": a linha da etapa 1 com o estado real, e o que depende do
dono (re-autorizar os canais, rodar o backfill).

O arquivo de changelog, no formato dos que já existem em `CHANGELOG.d/`.

- [ ] **Passo 2: marcar a spec**

Em `Docs/specs/001-retencao-youtube-analytics.md`: `**Status:** Entregue` e os critérios de pronto
marcados — só os que realmente passaram.

- [ ] **Passo 3: conferir os links**

Rodar: `python3 scripts/check-doc-links.py`
Esperado: `quebrados: 0 | avisos de âncora: 0`.

- [ ] **Passo 4: rodar a verificação inteira**

```bash
cd clip-processor && pytest
cd ../painel && vendor/bin/pest && vendor/bin/pint --test
cd .. && graphify update .
```

Esperado: tudo verde. `pytest` do clip-processor tem que passar **dentro da imagem**
(`docker compose build clip-processor` antes), porque não há bind mount para `src/`.

- [ ] **Passo 5: commit**

```bash
git add Docs CHANGELOG.d graphify-out
git commit -m "docs(retencao): documenta o coletor, a tabela e fecha a SPEC-001"
```

---

## Depois do plano, com o dono

1. Merge na `master` e deploy pela skill `finalizar-e-deploy`. O código pode ir **antes** da
   re-autorização: sem o escopo, a chamada falha sozinha e nada mais muda.
2. O dono gera os tokens novos com o escopo de Analytics (`python -m src.youtube_oauth <slug>`, um
   por canal) e leva os `token-{slug}.json` para `/app/youtube/` no servidor.
3. Rodar a carga retroativa uma vez:
   `docker compose exec clip-processor python -m src.retention_backfill --dias 400`.
4. Conferir `/painel/metricas` com retenção preenchida e medir quanto de cota o backfill consumiu —
   é o número que decide se a etapa 2 cabe no mesmo projeto do GCP.
