<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

return new class extends Migration
{
    /**
     * Trechos (chunks) das transcrições, unidade da busca textual e semântica.
     *
     * Criada por SQL puro por causa da coluna gerada `search_vector` e do tipo `vector`,
     * que o Blueprint não cobre por inteiro. Sem pgvector instalado, cria tudo menos a
     * coluna `embedding` e o índice HNSW (a busca textual continua funcionando).
     *
     * `transcription_jobs` não muda: os chunks apagam junto com o job (ON DELETE CASCADE).
     */
    public function up(): void
    {
        if (DB::getDriverName() !== 'pgsql') {
            return;
        }

        $temVector = DB::selectOne("SELECT 1 AS ok FROM pg_extension WHERE extname = 'vector'") !== null;

        $colunaEmbedding = $temVector
            ? "embedding        vector(384) NULL,\n                embedding_model  varchar(100) NULL,"
            : 'embedding_model  varchar(100) NULL,';

        DB::statement(<<<SQL
            CREATE TABLE IF NOT EXISTS transcript_chunks (
                id               bigserial PRIMARY KEY,
                job_id           bigint NOT NULL REFERENCES transcription_jobs (id) ON DELETE CASCADE,
                chunk_index      integer NOT NULL,
                content          text NOT NULL,
                start_seconds    real NULL,
                end_seconds      real NULL,
                token_estimate   integer NULL,
                {$colunaEmbedding}
                search_vector    tsvector GENERATED ALWAYS AS (to_tsvector('pt_unaccent', content)) STORED,
                created_at       timestamp NULL,
                CONSTRAINT transcript_chunks_job_chunk_unique UNIQUE (job_id, chunk_index)
            )
            SQL);

        DB::statement('CREATE INDEX IF NOT EXISTS transcript_chunks_search_gin ON transcript_chunks USING gin (search_vector)');
        DB::statement('CREATE INDEX IF NOT EXISTS transcript_chunks_trgm ON transcript_chunks USING gin (content gin_trgm_ops)');

        if ($temVector) {
            DB::statement(
                'CREATE INDEX IF NOT EXISTS transcript_chunks_embedding_hnsw ON transcript_chunks '
                .'USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)'
            );
        } else {
            Log::warning('busca_transcricoes: transcript_chunks criada SEM a coluna embedding e sem o índice HNSW '
                .'(extensão "vector" ausente). Só a busca textual funciona.');
        }
    }

    /** Só a tabela; extensões e configuração de texto ficam (ver migration anterior). */
    public function down(): void
    {
        if (DB::getDriverName() !== 'pgsql') {
            return;
        }

        DB::statement('DROP TABLE IF EXISTS transcript_chunks');
    }
};
