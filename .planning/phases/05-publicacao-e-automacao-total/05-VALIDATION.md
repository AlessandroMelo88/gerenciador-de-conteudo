# Phase 5 Validation: Publicacao e Automacao Total

## Strategy

Validar a fase em tres camadas:

1. Unit tests sem rede para quota, uploader e publisher.
2. Integration tests locais com mocks de MySQL/Redis/YouTube para status transitions.
3. Checkpoint manual controlado com upload privado no canal real.

## Automated Tests

Comandos esperados:

```bash
pytest clip-processor/tests/test_quota_manager.py
pytest clip-processor/tests/test_uploader.py
pytest clip-processor/tests/test_publisher.py
pytest clip-processor/tests/test_pipeline_runner.py
```

Acceptance checks:

- `QuotaManager` nunca permite mais de `min(MAX_UPLOADS_PER_DAY, 6)` uploads no dia local de Sao_Paulo.
- Fora de 19h-22h, nenhum upload e iniciado.
- `YouTubeUploader.upload_clip()` envia `title`, `description`, `tags`, `privacyStatus`, arquivo MP4 e thumbnail.
- `Publisher.publish_pending_clips()` muda `pending -> publishing -> published` em sucesso.
- Falha de upload gera `failed` + `upload_error`.
- Quota/horario bloqueados deixam clip em `pending`.
- Cleanup de raw video so acontece quando todos os clips do source video estao terminais.
- `run_pipeline_once()` chama polling/processamento e depois publicacao.

## Manual Checkpoint

1. Confirmar que `/app/token.json` tem `refresh_token`.
2. Aplicar `mysql/init/04-publishing-migration.sql`.
3. Subir containers.
4. Configurar `YOUTUBE_PRIVACY_STATUS=private` e `MAX_UPLOADS_PER_DAY=1` para primeiro teste.
5. Inserir ou reaproveitar um clip `generated_clips.status='pending'`.
6. Executar o runner uma vez.
7. Verificar no YouTube Studio:
   - video criado;
   - titulo, descricao e tags aplicados;
   - thumbnail customizada aplicada;
   - video privado.
8. Verificar MySQL:
   - clip em `published`;
   - `youtube_video_id` preenchido;
   - `published_at` preenchido;
   - `source_videos.status='published'` quando aplicavel.
9. Confirmar cleanup:
   - raw `source_videos.local_path` removido somente se nao havia outros clips pendentes do mesmo source.
10. Importar workflow n8n e validar retry/backoff.

## Non-goals

- Testes automatizados nao devem fazer upload real.
- Nao trocar o mecanismo RSS atual por YouTube API search.
- Nao apagar clips finais nem thumbnails no cleanup de raw video.
