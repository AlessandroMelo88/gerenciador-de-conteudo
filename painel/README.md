# Painel Canal de Cortes

Interface web (Laravel 12 + Inertia.js + React 19 + Tailwind CSS + shadcn UI) para o operador do pipeline Canal de Cortes:
- Gerenciar canais-fonte (RSS) e canais-destino (YouTube).
- Ver dashboard em tempo real do pipeline (uploads, cota, falhas).
- Aprovar/rejeitar clips gerados pela IA — mesmo efeito de `/aprovar` e `/rejeitar` no Telegram.

Roda dentro do container `php` compartilhado do stack `wordpress/`, servido
pelo `nginx` em `http://canaldecortes.local`, conectado à base `clips_automation`
(MySQL) e à instância `redis` já existentes.

## Setup local (uma vez)

1. Garantir que `wordpress/` docker-compose está rodando:
   ```
   docker compose -f wordpress/docker-compose.yml up -d nginx php mysql redis clip-processor
   ```

2. Adicionar host local:
   ```
   echo "127.0.0.1 canaldecortes.local" | sudo tee -a /etc/hosts
   ```

3. Instalar dependências PHP:
   ```
   docker exec -it php bash -c "cd /var/www/html/painel && composer install"
   ```

4. Gerar token do sidecar HTTP (compartilhado entre Laravel e clip-processor):
   ```
   openssl rand -hex 32
   ```
   Colar o hex em DOIS lugares:
   - `wordpress/.env` → `CLIP_PROCESSOR_INTERNAL_TOKEN=<hex>` (arquivo real lido pelo Docker Compose para o serviço `clip-processor`)
   - `canaldecortes/painel/.env` → `CLIP_PROCESSOR_INTERNAL_TOKEN=<hex>`

5. Preencher `canaldecortes/painel/.env` com `DB_PASSWORD` (mesmo valor de `CLIPS_DB_PASSWORD` do `canaldecortes/.env`).

6. Aplicar a migration de OAuth flag (idempotente):
   ```
   docker exec -i mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} clips_automation \
     < canaldecortes/mysql/init/07-panel-oauth-flag-migration.sql
   ```

7. Rodar migrations do Laravel (só cria users/sessions/cache/jobs em `clips_automation`):
   ```
   docker exec -it php bash -c "cd /var/www/html/painel && php artisan migrate --no-interaction"
   ```

8. Criar o operador (interativo — senha nunca ecoa):
   ```
   docker exec -it php php artisan --working-dir=/var/www/html/painel painel:create-user
   ```
   Email registrado: `alessandrobm1988@gmail.com`. Senha ≥10 chars.

9. Recriar container `clip-processor` para carregar `CLIP_PROCESSOR_INTERNAL_TOKEN`:
   ```
   docker compose -f wordpress/docker-compose.yml up -d --force-recreate clip-processor
   ```

10. Acessar: http://canaldecortes.local → login → dashboard.

## Reset de senha

```
docker exec -it php php artisan --working-dir=/var/www/html/painel painel:reset-password alessandrobm1988@gmail.com
```

## Preview MP4 dos clips

Este painel NÃO embute player HTML5 (por decisão explícita — reduz superfície de ataque).
Os arquivos MP4 ficam em `canaldecortes/videos/clips/` no filesystem local:
```
open canaldecortes/videos/clips/{clip_id}.mp4   # macOS
```

## Autorizar novo canal-destino (OAuth)

Após criar o canal-destino no painel, o painel mostra este comando copy-paste:
```
docker exec -it clip-processor python -m src.youtube_oauth --channel {slug}
```
Rodar no host, seguir o fluxo do Google. Volta ao painel: badge OAuth vira "authorized".

## Testes

- Suíte Laravel: `docker exec -it php bash -c "cd /var/www/html/painel && php artisan test"`
- Suíte Python: `docker exec -it clip-processor pytest tests/ -v`
