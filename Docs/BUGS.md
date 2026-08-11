# Backlog de bugs

Status: **FEITO** (corrigido e verificado) · **ABERTO** (confirmado, não corrigido) · **SUSPEITA** (evidência parcial, falta confirmar).

Ordem = prioridade. Última atualização: **11/08/2026**.

---

## 1. FEITO — Órfãos de download nunca eram apagados

**Corrigido em 11/08/2026** (`clip-processor/src/downloader.py`, `pipeline_runner.py`, `tests/test_downloader.py`).

Eram dois defeitos somados:

`_cleanup_partial` globava `output_path + '*.part'`, ou seja `<id>.mp4*.part`. O yt-dlp põe o sufixo de formato **antes** do `.mp4` (`QFDWHS3Oy3E.f298.mp4.part`), então o glob nunca casava com os streams separados. Também não cobria `.ytdl`, `.temp.mp4`, `.fNNN.webm` nem `.part-FragN.part`.

E mesmo corrigido, `_cleanup_partial` só roda no `except`. Quando o container morre (OOM, MySQL fora, disco cheio) o `except` nunca executa e o arquivo fica órfão para sempre.

Correção:
- glob passou a partir do prefixo sem extensão, filtrando por `_WORK_ARTIFACT_RE`
- nova `cleanup_stale_downloads(max_age_hours=6)` varre o primeiro nível de `/app/videos` e remove artefato de trabalho parado há 6h+; um `<id>.mp4` completo não casa com a regex
- `pipeline_runner.py` chama a limpeza no início de `_download_pending_videos`, antes de ocupar disco novo — o disk guard de 2GB mede o disco real, então órfão não limpo virava bloqueio de download

5 testes novos com os nomes reais tirados do disco de produção. Rodando: `28 passed`.

**Resíduo já removido à mão:** 7 arquivos, 4.39 GB (crashes de 27/07, 30/07 e 04/08).

**Pendente:** o código só passa a valer após `docker compose build clip-processor && docker compose up -d clip-processor` — não há bind mount para `src/`.

---

## 2. ABERTO — `_raw.mp4` nunca é apagado (maior consumidor de disco)

**Impacto: 8.5 GB, 259 arquivos.** O maior item do disco, acima dos vídeos fonte.

`video_processor.py:205` cria `<clip_id>_raw.mp4`, usa como entrada da queima de legenda e **nunca apaga**. O `_subtitled.mp4` é removido (linha 222) ou renomeado, mas o `_raw` some do fluxo e fica no disco.

Agrava: `_raw.mp4` não está em `clip_path` nem em nenhuma outra coluna. Nenhuma limpeza do painel o enxerga, e cruzar disco × banco por nome de arquivo o classifica como órfão de clip vivo (é exatamente a armadilha da regra 3 do `CLAUDE.md`).

**Onde corrigir:** `process_clip`, depois de `extract_thumbnail` e do `UPDATE` que grava `clip_path`. Só apagar após o final existir em disco.

**Guard obrigatório:** o `_raw` é necessário enquanto o clip está em `cutting`. Apagar apenas no caminho de sucesso, nunca no `except`.

**Limpeza retroativa:** dos 260 `_raw` em disco, 197 não têm clip final correspondente (4.9 GB) — mistura de clips que morreram no meio do processamento com clips cujo final foi apagado à mão pelo painel. Classificar cruzando com `generated_clips.status` antes de apagar; só é seguro para clips fora de `pending_cut`/`cutting`.

---

## 3. SUSPEITA — Thumbnail não aplicada nos vídeos longos no YouTube

**A geração local está correta e isso já foi verificado.** Dos 63 clips finais em disco, 25 são longos (1920x1080, 7–15 min) e **todos os 25 têm `.jpg` válido** em `videos/thumbnails/`, entre 204K e 388K. Nenhum clip, curto ou longo, está sem thumbnail. Não há ramo por formato: `video_processor.py:233` chama `extract_thumbnail` igual para os dois, e `uploader.py:114` chama `thumbnails().set` para qualquer clip com `thumbnail_path`.

Logo o defeito está **depois da geração**, na aplicação via API.

**Hipótese principal:** `thumbnails().set` retornando 403 — custom thumbnail exige canal verificado no YouTube. Ela roda **depois** do `videos.insert` (`uploader.py:114-123`), então o vídeo sobe e a exceção estoura em seguida, marcando o clip como `failed` com o motivo em `upload_error`. Bate com as "Últimas falhas 5" do painel. Shorts não expõem o sintoma porque o YouTube ignora thumbnail custom neles.

**Como confirmar:**
```sql
SELECT id, status, upload_error FROM generated_clips WHERE status='failed' ORDER BY id DESC LIMIT 20;
```
mais `docker compose logs clip-processor | grep -i thumb`.

**Se confirmado:** envolver o `thumbnails().set` em try/except próprio — o vídeo já subiu, falhar a thumbnail não deveria marcar o clip inteiro como `failed`.

---

## 4. ABERTO — Estados sem recuperação automática seguram arquivo em disco

`recover_stuck_downloads` (`src/db.py:112`) devolve `downloading` → `pending`, e `recover_stuck_selecting` cobre `selecting` → `downloaded`. **Não existe recuperação para `cutting` nem `publishing`** — o que trava nesses estados fica preso para sempre e segura o arquivo bruto.

Foi a causa do acúmulo que lotou o SSD no incidente de 27/07/2026. Detalhe do incidente em `CLAUDE.md`.

**Onde corrigir:** `main.py`, no bloco de recovery do boot, junto das duas que já existem.

---

## 5. ABERTO — `_subtitled.mp4` órfão

Mesma classe do bug 2, escala menor. `video_processor.py:207` cria o intermediário; ele é removido no caminho feliz, mas se o processo morrer entre a queima de legenda e o watermark o arquivo fica. Há pelo menos um em disco (`692_subtitled.mp4`).

Corrigir junto com o bug 2 — mesma varredura, mesmo guard.

---

## 6. ABERTO — Painel não consegue apagar o backlog de download

O card "Backlog download" mostra 1062 vídeos `pending` sem arquivo em disco. Nenhuma ação do painel apaga essas **linhas**:

- `DashboardController::bulkDeleteVideos` pula `blank($video->local_path)` como *skipped* — só apaga arquivo
- `SourceVideoController::bulkDeleteFiles` idem
- só `purgeOld` → `internal_api.purge_old_videos` apaga linha, e apenas por data

Resultado: o operador vê 1062 no painel e não tem botão que resolva.

**Complicação a considerar antes de "resolver":** `purge_old_videos` também apaga as chaves Redis `video:<id>` de dedup. Os vídeos purgados deixam de estar "vistos" e voltam a ser inseridos como `pending` no próximo poll RSS. Não voltam a baixar (`FRESHNESS_DAYS=1` barra publicado antes de ontem), mas o contador reenche. Purgar trata o sintoma; a causa é o RSS ingerir mais do que a janela consome.

---

## 7. ABERTO — 4 testes de `test_pipeline_runner.py` falhando

Falhas **pré-existentes**, confirmadas em 11/08/2026 rodando a suíte com as mudanças do bug 1 em stash — mesmas 4 falhas antes e depois.

- `test_scheduler_compatible_coalesce`: `ModuleNotFoundError: No module named 'flask'` — o host não tem as dependências do sidecar instaladas
- os outros 3: `StopIteration` em mock de cursor com `side_effect` esgotado

Rodar a suíte dentro do container resolveria o caso do flask. Os mocks precisam de revisão à parte.

---

## 8. ABERTO — Docker Desktop travado sob pressão de disco

Em 11/08/2026, com o SSD em 85% (2.1 GiB livres), `docker ps` ficou pendurado indefinidamente em três tentativas seguidas — daemon inacessível, sem MySQL e sem logs. Liberar 4.39 GB não destravou; exige restart do Docker Desktop.

Não é bug do projeto, mas é o modo de falha que **esconde todos os outros**: sem Docker não há banco nem log, e o diagnóstico do bug 3 depende dos dois. Registrar aqui porque na próxima vez o sintoma vai parecer outra coisa.
