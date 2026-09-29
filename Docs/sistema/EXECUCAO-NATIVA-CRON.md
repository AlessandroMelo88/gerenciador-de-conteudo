# Workers nativos com cron

Os workers do `clip-processor` podem rodar diretamente em Linux ou macOS, sem
Docker. O host precisa ter Python 3.11+, FFmpeg/ffprobe, PostgreSQL com o schema
do painel e Redis acessíveis. A aplicação web não precisa rodar no mesmo host.

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

O instalador agenda polling a cada 20 minutos, download/IA/render a cada 15,
manutenção a cada 30 e a etapa de publicação a cada hora. A publicação só
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
