# Painel Canal de Cortes

Interface web (Laravel 13 + Inertia.js + React 19 + Tailwind CSS + shadcn/ui) para o operador do
pipeline Canal de Cortes:

- gerenciar canais-fonte (RSS) e canais-destino (YouTube);
- acompanhar uploads, cota e falhas;
- aprovar ou rejeitar clips gerados pela IA;
- operar a fila de vídeos e a transcrição local.

## Setup local

O painel faz parte do Compose da raiz do projeto e usa PostgreSQL e Redis privados do próprio stack.
Consulte [`../README.md`](../README.md) para subir os serviços e [`../Docs/DESENVOLVIMENTO.md`](../Docs/DESENVOLVIMENTO.md)
para as ferramentas de qualidade.

```bash
cp .env.example .env
make setup-panel
docker compose run --rm panel-init
docker compose up -d php queue scheduler nginx clip-processor
```

O `panel-init` executa todas as migrations Laravel, incluindo o schema do pipeline. Consulte o estado
com:

```bash
docker compose exec php php artisan migrate:status
```

Para criar o primeiro operador (senha nunca é exibida):

```bash
docker compose exec php php artisan painel:create-user
```

O painel fica em [http://localhost:8088](http://localhost:8088).

## OAuth de canal-destino

Depois de cadastrar o canal no painel, execute o comando sugerido pela interface dentro do container:

```bash
docker compose exec clip-processor python -m src.youtube_oauth --channel <slug>
```

## Testes e qualidade

```bash
make lint
make test-python
make test-php  # execute no container PHP; use uma base de teste isolada
```

Para a suíte completa local, use `make ci` e siga as orientações de banco em
[`../Docs/DESENVOLVIMENTO.md`](../Docs/DESENVOLVIMENTO.md).
