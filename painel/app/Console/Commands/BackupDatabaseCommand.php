<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\File;
use Symfony\Component\Process\Process;

class BackupDatabaseCommand extends Command
{
    protected $signature = 'db:backup 
                            {--connection= : Conexao do banco a ser feito o backup (padrao: DB_CONNECTION ativo)}
                            {--keep=7 : Quantidade de dias para reter backups antigos (0 para desativar purga)}';

    protected $description = 'Gera backup compactado (.sql.gz) do banco de dados (suporta MySQL, PostgreSQL e SQLite) com politica de retencao';

    public function handle(): int
    {
        $connectionName = $this->option('connection') ?: config('database.default');
        $config = config("database.connections.{$connectionName}");

        if (!$config) {
            $this->error("Conexao '{$connectionName}' nao encontrada em config/database.php.");
            return self::FAILURE;
        }

        $driver = $config['driver'] ?? 'unknown';
        $this->info("Iniciando backup da conexao '{$connectionName}' (driver: {$driver})...");

        $backupDir = storage_path('app/backups');
        if (!File::isDirectory($backupDir)) {
            File::makeDirectory($backupDir, 0755, true);
        }

        $timestamp = now()->format('Y-m-d_His');
        $filename = "backup_{$connectionName}_{$timestamp}.sql.gz";
        $targetPath = "{$backupDir}/{$filename}";

        $success = false;

        // Verifica se ferramentas nativas estao disponiveis
        if ($driver === 'pgsql' && $this->commandExists('pg_dump')) {
            $success = $this->backupPostgres($config, $targetPath);
        } elseif (($driver === 'mysql' || $driver === 'mariadb') && $this->commandExists('mysqldump')) {
            $success = $this->backupMysql($config, $targetPath);
        }

        // Se nao tem ferramenta nativa ou falhou, usa exportador PHP agnostico
        if (!$success) {
            $this->line("Usando exportador agnostico PHP PDO...");
            $success = $this->backupGenericPhp($connectionName, $targetPath);
        }

        if (!$success || !file_exists($targetPath) || filesize($targetPath) <= 30) {
            $this->error("Falha ao gerar o arquivo de backup.");
            if (file_exists($targetPath)) {
                unlink($targetPath);
            }
            return self::FAILURE;
        }

        $sizeKb = round(filesize($targetPath) / 1024, 2);
        $this->info("✓ Backup gerado com sucesso: {$filename} ({$sizeKb} KB)");
        $this->line("Caminho: {$targetPath}");

        // Retencao
        $keepDays = (int)$this->option('keep');
        if ($keepDays > 0) {
            $this->pruneOldBackups($backupDir, $connectionName, $keepDays);
        }

        return self::SUCCESS;
    }

    protected function commandExists(string $cmd): bool
    {
        $process = Process::fromShellCommandline("which {$cmd}");
        $process->run();
        return $process->isSuccessful();
    }

    protected function backupMysql(array $config, string $targetPath): bool
    {
        $host = $config['host'] ?? '127.0.0.1';
        $port = $config['port'] ?? '3306';
        $database = $config['database'] ?? '';
        $username = $config['username'] ?? 'root';
        $password = $config['password'] ?? '';

        $cmd = sprintf(
            'mysqldump --host=%s --port=%s --user=%s --password=%s --single-transaction --quick --skip-lock-tables %s | gzip > %s',
            escapeshellarg($host),
            escapeshellarg($port),
            escapeshellarg($username),
            escapeshellarg($password),
            escapeshellarg($database),
            escapeshellarg($targetPath)
        );

        $process = Process::fromShellCommandline($cmd);
        $process->setTimeout(600);
        $process->run();

        return $process->isSuccessful() && file_exists($targetPath) && filesize($targetPath) > 50;
    }

    protected function backupPostgres(array $config, string $targetPath): bool
    {
        $host = $config['host'] ?? '127.0.0.1';
        $port = $config['port'] ?? '5432';
        $database = $config['database'] ?? '';
        $username = $config['username'] ?? 'postgres';
        $password = $config['password'] ?? '';

        $cmd = sprintf(
            'PGPASSWORD=%s pg_dump --host=%s --port=%s --username=%s --no-owner --no-privileges %s | gzip > %s',
            escapeshellarg($password),
            escapeshellarg($host),
            escapeshellarg($port),
            escapeshellarg($username),
            escapeshellarg($database),
            escapeshellarg($targetPath)
        );

        $process = Process::fromShellCommandline($cmd);
        $process->setTimeout(600);
        $process->run();

        return $process->isSuccessful() && file_exists($targetPath) && filesize($targetPath) > 50;
    }

    protected function backupGenericPhp(string $connectionName, string $targetPath): bool
    {
        try {
            $rawTables = DB::connection($connectionName)->getSchemaBuilder()->getTableListing();
            $tables = array_map(fn($t) => preg_replace('/^.*\./', '', $t), $rawTables);
        } catch (\Throwable $ex) {
            $this->error("Erro ao listar tabelas: " . $ex->getMessage());
            return false;
        }

        $gz = gzopen($targetPath, 'w9');
        if (!$gz) {
            return false;
        }

        gzwrite($gz, "-- Backup gerado via Artisan db:backup\n");
        gzwrite($gz, "-- Data: " . now()->toIso8601String() . "\n");
        gzwrite($gz, "-- Conexao: {$connectionName}\n\n");

        foreach ($tables as $table) {
            $count = DB::connection($connectionName)->table($table)->count();
            gzwrite($gz, "-- Tabela: {$table} ({$count} registros)\n");

            if ($count === 0) {
                continue;
            }

            $perPage = 200;
            $pages = ceil($count / $perPage);
            for ($page = 1; $page <= $pages; $page++) {
                $rows = DB::connection($connectionName)->table($table)->forPage($page, $perPage)->get();
                foreach ($rows as $row) {
                    $values = array_map(function ($val) {
                        if (is_null($val)) return 'NULL';
                        return "'" . addslashes((string)$val) . "'";
                    }, (array)$row);

                    $columns = implode(', ', array_keys((array)$row));
                    $vals = implode(', ', $values);
                    gzwrite($gz, "INSERT INTO {$table} ({$columns}) VALUES ({$vals});\n");
                }
            }

            gzwrite($gz, "\n");
        }

        gzclose($gz);
        return true;
    }

    protected function pruneOldBackups(string $backupDir, string $connectionName, int $keepDays): void
    {
        $cutoff = now()->subDays($keepDays);
        $files = File::glob("{$backupDir}/backup_{$connectionName}_*.sql.gz");
        $deleted = 0;

        foreach ($files as $file) {
            if (File::lastModified($file) < $cutoff->getTimestamp()) {
                File::delete($file);
                $deleted++;
            }
        }

        if ($deleted > 0) {
            $this->info("Purga de backups: {$deleted} backup(s) antigo(s) removido(s) (janela de {$keepDays} dias).");
        }
    }
}
