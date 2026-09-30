<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

return new class extends Migration
{
    /**
     * Base da busca nas transcrições: extensões e a configuração de texto em português.
     *
     * - `pg_trgm`: busca aproximada (erro de digitação, trecho parcial).
     * - `unaccent`: "acao" acha "ação".
     * - `vector` (pgvector): busca semântica por embeddings.
     * - Configuração `pt_unaccent`: stemmer português com `unaccent` na frente. Ao
     *   contrário de chamar `unaccent()` direto (STABLE), usar a configuração dentro de
     *   `to_tsvector('pt_unaccent', ...)` é IMMUTABLE e pode ir numa coluna GENERATED.
     *
     * Tolerante de propósito: fora do PostgreSQL não faz nada, e se o servidor não tem o
     * pgvector instalado (o Postgres compartilhado de desenvolvimento não tem) segue sem
     * ele e avisa no log — a busca textual funciona, só a semântica fica desligada. Em
     * produção a ausência do pgvector derruba a migration de propósito: significa que a
     * imagem do Postgres não foi trocada (ver DEPLOY.md), e seguir criaria a tabela sem
     * a coluna `embedding`.
     */
    public function up(): void
    {
        if (DB::getDriverName() !== 'pgsql') {
            return;
        }

        DB::statement('CREATE EXTENSION IF NOT EXISTS pg_trgm');
        DB::statement('CREATE EXTENSION IF NOT EXISTS unaccent');

        $vectorDisponivel = DB::selectOne("SELECT 1 AS ok FROM pg_available_extensions WHERE name = 'vector'") !== null;

        if ($vectorDisponivel) {
            DB::statement('CREATE EXTENSION IF NOT EXISTS vector');
        } elseif (app()->environment('production')) {
            throw new RuntimeException(
                'Extensão pgvector indisponível no Postgres de produção. Recrie o serviço postgres '
                .'com a imagem de docker/postgres antes do deploy (runbook no DEPLOY.md).'
            );
        } else {
            Log::warning('busca_transcricoes: extensão "vector" indisponível neste Postgres; '
                .'a busca semântica fica desligada (só texto). Use scripts/dev-pgvector.sh.');
        }

        $existe = DB::selectOne("SELECT 1 AS ok FROM pg_ts_config WHERE cfgname = 'pt_unaccent'") !== null;

        if (! $existe) {
            DB::statement('CREATE TEXT SEARCH CONFIGURATION pt_unaccent (COPY = portuguese)');
            DB::statement(
                'ALTER TEXT SEARCH CONFIGURATION pt_unaccent '
                .'ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem'
            );
        }
    }

    /**
     * Não remove extensões nem a configuração: outras partes do banco podem depender delas
     * e `DROP EXTENSION` levaria junto qualquer coluna `vector`. A tabela é desfeita na
     * migration seguinte.
     */
    public function down(): void
    {
    }
};
