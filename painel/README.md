# Painel Canal de Cortes

Painel administrativo Laravel 13 + Filament 5.4 para gerenciar canais-fonte,
canais-destino, monitorar o pipeline em tempo real e aprovar/rejeitar clips —
sem SQL manual, sem depender do Telegram.

Roda dentro do container `php` compartilhado do stack `wordpress/`, servido
pelo `nginx` em `http://canaldecortes.local`, conectado à base `clips_automation`
(MySQL) e à instância `redis` já existentes.

## Setup local

```bash
# 1. Adicionar o host local (uma vez)
echo "127.0.0.1 canaldecortes.local" | sudo tee -a /etc/hosts

# 2. Subir os serviços necessários
docker compose -f wordpress/docker-compose.yml up -d nginx php mysql redis

# 3. Instalar dependências PHP dentro do container php
docker exec -it php bash -c "cd /var/www/html/painel && composer install"

# 4. Preencher canaldecortes/painel/.env com DB_PASSWORD (CLIPS_DB_PASSWORD
#    real do canaldecortes/.env) e CLIP_PROCESSOR_INTERNAL_TOKEN

# 5. Criar o usuário operador (comando será criado no Plan 08-04)
docker exec -it php bash -c "cd /var/www/html/painel && php artisan painel:create-user"
```

## URL

Acesse o painel em: `http://canaldecortes.local`

Login em `http://canaldecortes.local/admin/login` — usuário único (single-user),
criado via `php artisan painel:create-user`.

## Preview MP4

O painel NÃO tem player HTML5 embutido (reduz superfície de ataque e complexidade
de nginx). Os arquivos de vídeo gerados ficam disponíveis no filesystem local em
`canaldecortes/videos/clips/` — para assistir um clip antes de aprovar, abra o
arquivo `.mp4` correspondente diretamente no Finder ou no VLC.
