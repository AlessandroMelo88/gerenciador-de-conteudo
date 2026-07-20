# Canal de Cortes — instruções de trabalho

Arquitetura as-built: `ARCHITECTURE.md`. Os dois `README.md` estão desatualizados (dizem "Filament";
o painel é Inertia + React desde `dca6e44`).

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
