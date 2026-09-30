<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;

/**
 * Só diagnóstico. O chunking e o backfill vetorial vivem em Python
 * (scripts/transcript_indexer.py --backfill); aqui se confere o que falta.
 */
class IndexarTranscricoes extends Command
{
    protected $signature = 'transcricoes:indexar {--status : Mostra jobs sem chunks e chunks sem embedding}';

    protected $description = 'Situação do índice de busca das transcrições (o backfill é feito pelo indexador Python)';

    public function handle(): int
    {
        if (DB::getDriverName() !== 'pgsql') {
            $this->warn('Índice de busca só existe no PostgreSQL.');

            return self::SUCCESS;
        }

        $colunas = collect(DB::select(
            "SELECT column_name FROM information_schema.columns
             WHERE table_schema = current_schema() AND table_name = 'transcript_chunks'"
        ))->pluck('column_name');

        if ($colunas->isEmpty()) {
            $this->error('Tabela transcript_chunks não existe. Rode as migrations.');

            return self::FAILURE;
        }

        $semChunks = (int) DB::scalar(
            "SELECT COUNT(*) FROM transcription_jobs j
             WHERE j.status = 'done'
               AND NOT EXISTS (SELECT 1 FROM transcript_chunks c WHERE c.job_id = j.id)"
        );
        $totalChunks = (int) DB::scalar('SELECT COUNT(*) FROM transcript_chunks');
        $semVetor = $colunas->contains('embedding')
            ? (int) DB::scalar('SELECT COUNT(*) FROM transcript_chunks WHERE embedding IS NULL')
            : null;

        $this->table(['Indicador', 'Quantidade'], [
            ['Transcrições prontas sem chunks', $semChunks],
            ['Chunks no total', $totalChunks],
            ['Chunks sem embedding', $semVetor ?? 'coluna embedding ausente'],
        ]);

        if ($semChunks > 0 || $semVetor) {
            $this->line('Para indexar: python scripts/transcript_indexer.py --backfill [--job N] [--reindex]');
        }

        return self::SUCCESS;
    }
}
