# Workers nativos com cron

Os workers do `clip-processor` podem rodar diretamente em Linux ou macOS, sem
Docker. O host precisa ter Python 3.11+, FFmpeg/ffprobe, PostgreSQL com o schema
do painel e Redis acessíveis. A aplicação web não precisa rodar no mesmo host.

## Banco do cron do Hacker Libertário

Na máquina verificada em 29/09/2026, o worker nativo conecta a `clips_automation` no PostgreSQL
18.3 do Homebrew, em `127.0.0.1:5432`. Essa conexão foi confirmada pelo mesmo acesso configurado no
`.env`; `pgvector` ainda não está instalado/disponível. PostgreSQL 18 é o alvo deste cron — não
regredir para 17. A decisão registrada e as pendências estão em
[ADR-0007](../ADR/0007-postgresql-18-nativo-pgvector.md).

O PostgreSQL da produção e o serviço PostgreSQL do Compose são outros ambientes. A imagem do
Compose declara PostgreSQL 17, enquanto o container observado nesta máquina estava em 16.15. Não
trocar a imagem sobre o volume existente sem backup validado e migração de versão principal.

## Configuração

1. Instale e inicie PostgreSQL e Redis no host. Configure a conexão com o banco
   no `.env`; para serviços locais, use `127.0.0.1`. Também é possível apontar
   para servidores remotos.
2. Execute `bash scripts/install_native_worker.sh`. Se ainda não existir `.env`,
   o script cria uma cópia local de `.env.native.example` sem sobrescrever um
   arquivo existente, cria o virtualenv e instala as dependências Python.
3. Edite `.env`: informe senha do banco, `GROQ_API_KEY`, client secrets e tokens
   do YouTube. Configure também `LARAVEL_NOTIFY_URL`, `LARAVEL_HOST_HEADER` e
   `CLIP_PROCESSOR_INTERNAL_TOKEN` para o painel receber notificações. O token
   precisa ser igual ao do painel. O pipeline começa pausado
   (`PIPELINE_ENABLED=false`); ligue-o depois de validar conexões e destinos.
4. Confira os diretórios `VIDEOS_DIR`, `ASSETS_DIR`, `BRANDING_DIR` e
   `YOUTUBE_DIR`. Os caminhos relativos do exemplo são resolvidos a partir da
   raiz do repositório. Caminhos Docker padrão (`/app/...`) são convertidos para
   pastas locais pelo runner nativo.
5. Instale o agendamento no crontab do usuário:

   ```bash
   clip-processor/.venv/bin/python scripts/install_native_cron.py
   ```

O instalador agenda polling a cada 2 horas; download, IA e render rodam uma vez
por hora, nos minutos 15, 30 e 45; manutenção roda a cada 3 horas; publicação
roda a cada hora. A publicação só
acontece nos horários permitidos pela aplicação, em `America/Sao_Paulo`:

- Vídeos longos: 06h, 14h e 22h, separados por oito horas.
- Shorts: 12h e 20h, nas janelas de pico.
- No máximo um upload por canal em cada horário configurado; limites diários
  e de formato continuam aplicados pelo Redis.

Os horários e cotas podem ser alterados no `.env` (`LONG_UPLOAD_HOURS`,
`SHORTS_PEAK_HOURS`, `MAX_LONGO_UPLOADS_PER_DAY`,
`MAX_CURTO_UPLOADS_PER_DAY` e `MAX_UPLOADS_PER_DAY`). Após mudar os horários,
o cron pode continuar como está, pois chama a etapa de publicação de hora em
hora e o worker aplica as novas janelas.

A frequência de polling limita a rapidez com que novos vídeos entram no pipeline:
com o valor atual, uma fonte pode esperar até duas horas para ser consultada.
Considere esse intervalo como latência operacional, não como garantia de alcance.

Cada etapa tem um lock local para impedir sobreposição no host e usa também o
lock Redis existente. Logs ficam em `var/native-worker/logs/` e são rotacionados
por etapa. Para conferir o crontab, use `crontab -l`. Para remover somente as
entradas deste projeto e preservar as demais:

```bash
clip-processor/.venv/bin/python scripts/install_native_cron.py --remove
```

O modo nativo mantém as mesmas linhas no PostgreSQL. A limpeza de disco remove
arquivos locais, enquanto o código continua preservando transcrições, texto e
metadados pesquisáveis na base. Registros antigos com caminhos `/app/videos/`
são traduzidos para `VIDEOS_DIR` no host.
