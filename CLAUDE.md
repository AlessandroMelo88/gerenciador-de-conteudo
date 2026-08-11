# Canal de Cortes — instruções de trabalho

**Comece por `Docs/README.md`** — é o índice: estado atual, backlog de bugs com status, plano de
migração para a Oracle e referência de cada serviço. Toda conversa nova abre por ali; status de
tarefa mora nesses arquivos, não no histórico de conversa.

Arquitetura as-built: `ARCHITECTURE.md`. O painel é Inertia.js + React 19 + shadcn UI desde `dca6e44`.

**Isolamento:** o `docker-compose.yml` da raiz `wordpress/` é compartilhado com outros projetos
(kelnab, feeb, placebeads, riodelux, gringo). Mexer **apenas** no serviço `clip-processor` e nos
paths sob `canaldecortes/`.

---

## Regras para operações destrutivas

Valem para `rm`, `DELETE`/`DROP`/`TRUNCATE`, `docker prune|rm|down -v`, `git clean|reset --hard`.

### 1. Listar antes de apagar — sempre em duas etapas

Nunca descobrir e apagar no mesmo comando. Primeiro gerar a lista e **mostrar a contagem e o tamanho**;
só então apagar a partir dessa lista.

```bash
# etapa 1 — materializa o alvo e confere
comm -23 disco.txt manter.txt > alvos.txt && wc -l < alvos.txt && du -ch $(cat alvos.txt)
# etapa 2 — apaga a partir da lista revisada
tr '\n' '\0' < alvos.txt | xargs -0 rm -f
```

Se a etapa 1 vier com contagem inesperada (muito maior ou zero), parar e investigar — não ajustar
o comando até "dar certo".

### 2. Caminhos absolutos, e verificar que o `rm` funcionou

`rm` em loop com caminho relativo já falhou **silenciosamente** aqui (o `cd` não pegou, nada foi
apagado, e o `UPDATE` seguinte no banco rodou mesmo assim — deixando banco e disco divergentes).

- Usar sempre caminho absoluto ou `rm -v`.
- Conferir o resultado depois (`ls`, contagem), não assumir sucesso.
- Apagar arquivo **antes** de atualizar o banco, nunca o contrário.

### 3. Ao cruzar banco × disco, filtrar pela chave — não pelo nome do arquivo

Um clip tem mais arquivos em disco do que colunas no banco: `<id>.mp4` e `<id>.jpg` estão em
`clip_path`/`thumbnail_path`, mas `<id>.srt` e `<id>_raw.mp4` **não estão em lugar nenhum**.
Comparar nomes contra as colunas marca esses auxiliares como órfãos e apaga arquivo de clip vivo.

**Certo:** extrair o id (prefixo numérico antes de `.` ou `_`) e comparar com `SELECT id FROM generated_clips`.

Regra geral: antes de classificar algo como órfão, confirmar que a fonte da verdade lista *todos* os
artefatos daquele registro. Se não lista, filtrar pela chave.

### 4. Nunca podar Docker às cegas

`docker system prune -f` remove containers **parados** e `docker image prune -af` remove a imagem
que ficou órfã em seguida. Foi assim que o `clip-processor` sumiu por completo — junto com os logs
que diriam por que ele havia caído.

Antes de podar: `docker ps -a` e `docker compose ps`. Se um serviço do projeto estiver parado,
**investigar (`docker compose logs`) antes**; nunca podar por cima de evidência de falha.
Preferir alvo específico a `prune` genérico.

### 5. Backup antes de DELETE em massa

```bash
docker exec mysql mysqldump -uroot -p"$P" clips_automation source_videos generated_clips > backup.sql
```

As FKs de `generated_clips` **não** têm `ON DELETE CASCADE` — apagar `source_videos` com clips
vinculados falha por FK. Ordem correta: clips primeiro, depois vídeos.

### 6. Confirmar escopo quando "antigo/inútil" for ambíguo

Estado transitório (`selecting`, `cutting`, `publishing`) parece lixo mas pode ser trabalho em curso;
registro `published` é histórico do que foi ao ar. Quando o pedido não distingue os dois, perguntar
antes — a diferença já foi de 5 para 27 vídeos numa mesma frase.

### 7. Arquivo em uso pelo pipeline

O raw de um vídeo ainda é necessário se algum clip dele está em `pending_cut` ou `cutting` —
`process_clip` lê o arquivo original na hora de cortar. O guard do sidecar
(`delete_source_video_file`) checa só `source_videos.status`, que nunca recebe `cutting`, então
**ele não protege esse caso**. Checar `generated_clips.status` na mão antes de apagar raw.

---

## Estados que não têm recuperação automática

`recover_stuck_downloads` (`src/db.py:112`) só devolve `downloading` → `pending`. Não existe
recuperação para `selecting`, `cutting` ou `publishing` — o que trava nesses estados fica preso
para sempre e segura o arquivo em disco. Foi a causa do acúmulo que lotou o SSD.

---

## Reset de fila / limpar Redis — o que cada coisa faz

Incidente 27/07/2026: nada subia desde 24/07. Cadeia: HD 99% cheio → MySQL caiu
(`Can't connect to MySQL server ... Errno 111` em loop) → pipeline travou → clip ficou preso em
`publishing` (estado sem recuperação, ver acima). Destravar exigiu: liberar disco, subir MySQL,
apagar o clip travado e purgar o backlog.

**A fila NÃO mora no Redis.** Fila = MySQL (`source_videos`, `generated_clips`). O Redis guarda só:

- chaves `video:<id>` (TTL 30 dias) — marca "vídeo já visto" pra dedup;
- contador de quota diária `youtube_uploads:<data>` (e `:<canal>` / `:<formato>`).

Consequência que morde: **apagar as chaves `video:*` faz os vídeos deletados voltarem** no próximo
poll RSS (deixam de estar "vistos"). Para purgar de vez, apagar as linhas do MySQL e **manter** as
chaves dedup. Nunca `FLUSHALL` achando que "reseta a fila" — isso ressuscita todo o backlog e zera
a quota junto.

**Contador de quota travado ≠ fila travada.** Se o problema for só "não sobe mais hoje", conferir
`youtube_uploads:<hoje>` no Redis; resetar só essa chave, não o dedup.

**Filtro de frescor no download:** `pipeline_runner.py` (`FRESHNESS_DAYS=1`) só baixa `pending` com
`published_at` de hoje/ontem. Vídeo pendente mais velho que isso nunca baixa — fica em `pending`
pra sempre sem ser lixo de verdade. Considerar isso antes de classificar `pending` antigo como
backlog descartável.

---

## "Vídeos duplicados na fila" — na verdade título duplicado

`ANTHROPIC_API_KEY` vazio (config normal de operação, ver acima) fazia `metadata_generator.py`
falhar sempre e cair no fallback burro: título = título bruto do vídeo original. Como o seletor
tira até 3 momentos por vídeo, os 3 clips saíam com título idêntico — parecia vídeo duplicado na
fila de aprovação, mas eram clips diferentes (trechos diferentes) do mesmo vídeo.

Fix (27/07/2026): `metadata_generator.py` ganhou o mesmo fallback Groq que `selector.py` já usava
(`_select_via_groq`). Ordem agora: Anthropic → Groq → título bruto só se as duas falharem.
Qualquer novo caminho de IA nesse pipeline devia nascer com fallback Groq de cara — não replicar
esse buraco em outro lugar.

**Editar código do clip-processor exige rebuild + restart** — não há bind mount pro `src/`, a
imagem embute o código no build. `docker compose build clip-processor && docker compose up -d
clip-processor` (isolado, não sobe mysql/redis nem outros projetos).

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
