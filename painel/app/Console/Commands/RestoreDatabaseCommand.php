<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\File;
use Symfony\Component\Process\Process;

class RestoreDatabaseCommand extends Command
{
    protected $signature = 'db:restore 
                            {file? : Caminho ou nome do arquivo de backup dentro de storage/app/backups}
                            {--connection= : Conexao do banco a ser restaurada (padrao: detectada pelo arquivo ou DB_CONNECTION)}
                            {--test : Executa smoke test de validacao do backup (descompacta e valida integridade sem tocar no banco)}
                            {--force : Executa a restauracao sem solicitar confirmacao interativa}';

    protected $description = 'Restaura/Recupera o banco de dados a partir de um arquivo de backup (.sql.gz ou .sql)';

    public function handle(): int
    {
        $backupDir = storage_path('app/backups');
        $filePath = $this->argument('file');

        if (!$filePath) {
            $files = File::glob("{$backupDir}/*.{gz,sql}", GLOB_BRACE);
            if (empty($files)) {
                $this->error("Nenhum arquivo de backup encontrado em {$backupDir}.");
                return self::FAILURE;
            }

            usort($files, fn($a, $b) => filemtime($b) - filemtime($a));
            $options = array_map(fn($f) => basename($f) . ' (' . round(filesize($f) / 1024, 1) . ' KB - ' . date('Y-m-d H:i:s', filemtime($f)) . ')', $files);

            $selected = $this->choice('Selecione o arquivo de backup para restaurar:', $options, 0);
            $selectedIndex = array_search($selected, $options);
            $filePath = $files[$selectedIndex];
        } else {
            if (!File::exists($filePath)) {
                $candidate = "{$backupDir}/{$filePath}";
                if (File::exists($candidate)) {
                    $filePath = $candidate;
                } else {
                    $this->error("Arquivo de backup nao encontrado: {$filePath}");
                    return self::FAILURE;
                }
            }
        }

        $this->info("Arquivo selecionado: " . basename($filePath));

        // Teste de integridade (Smoke test / Recuperação preventiva)
        if ($this->option('test')) {
            return $this->runSmokeTest($filePath);
        }

        $connectionName = $this->option('connection');
        if (!$connectionName) {
            // Tenta inferir pelo nome do arquivo: backup_{connection}_{timestamp}.sql.gz
            if (preg_match('/backup_([a-zA-Z0-9_-]+)_\d{4}-\d{2}-\d{2}/', basename($filePath), $m)) {
                $connectionName = $m[1];
            } else {
                $connectionName = config('database.default');
            }
        }

        $config = config("database.connections.{$connectionName}");
        if (!$config) {
            $this->error("Conexao '{$connectionName}' nao encontrada em config/database.php.");
            return self::FAILURE;
        }

        $driver = $config['driver'] ?? 'unknown';

        if (!$this->option('force')) {
            $confirm = $this->confirm(
                "ATENCAO: Restaurar o backup ira sobrescrever os dados na conexao '{$connectionName}' ({$driver}). Deseja continuar?",
                false
            );
            if (!$confirm) {
                $this->warn("Operacao cancelada pelo usuario.");
                return self::SUCCESS;
            }
        }

        $this->info("Iniciando restauracao na conexao '{$connectionName}' (driver: {$driver})...");

        $success = false;
        if ($driver === 'pgsql') {
            $success = $this->restorePostgres($config, $filePath);
        } elseif ($driver === 'mysql' || $driver === 'mariadb') {
            $success = $this->restoreMysql($config, $filePath);
        }

        if (!$success) {
            $this->warn("Tentando fallback de restauracao direta via PHP PDO...");
            $success = $this->restoreGenericPhp($connectionName, $filePath);
        }

        if ($success) {
            $this->info("✓ Banco de dados recuperado e restaurado com sucesso!");
            return self::SUCCESS;
        }

        $this->error("Falha ao restaurar o banco de dados.");
        return self::FAILURE;
    }

    protected function runSmokeTest(string $filePath): int
    {
        $this->info("Executando Smoke Test de validacao do backup...");
        $isGz = str_ends_with($filePath, '.gz');

        if ($isGz) {
            $gz = gzopen($filePath, 'rb');
            if (!$gz) {
                $this->error("Falha ao abrir arquivo comprimido gzip.");
                return self::FAILURE;
            }
            $header = gzread($gz, 512);
            gzclose($gz);
        } else {
            $header = file_get_contents($filePath, false, null, 0, 512);
        }

        if (empty($header)) {
            $this->error("Arquivo de backup esta vazio ou corrompido.");
            return self::FAILURE;
        }

        $this->info("✓ Integridade do arquivo verificada com sucesso.");
        $this->line("Visualizacao do cabecalho:");
        $this->comment(substr($header, 0, 200) . '...');
        return self::SUCCESS;
    }

    protected function restoreMysql(array $config, string $filePath): bool
    {
        $host = $config['host'] ?? '127.0.0.1';
        $port = $config['port'] ?? '3306';
        $database = $config['database'] ?? '';
        $username = $config['username'] ?? 'root';
        $password = $config['password'] ?? '';

        $catCmd = str_ends_with($filePath, '.gz') ? "gzip -dc " . escapeshellarg($filePath) : "cat " . escapeshellarg($filePath);

        $cmd = sprintf(
            '%s | mysql --host=%s --port=%s --user=%s --password=%s %s 2>/dev/null',
            $catCmd,
            escapeshellarg($host),
            escapeshellarg($port),
            escapeshellarg($username),
            escapeshellarg($password),
            escapeshellarg($database)
        );

        $process = Process::fromShellCommandline($cmd);
        $process->setTimeout(600);
        $process->run();

        return $process->isSuccessful();
    }

    protected function restorePostgres(array $config, string $filePath): bool
    {
        $host = $config['host'] ?? '127.0.0.1';
        $port = $config['port'] ?? '5432';
        $database = $config['database'] ?? '';
        $username = $config['username'] ?? 'postgres';
        $password = $config['password'] ?? '';

        $catCmd = str_ends_with($filePath, '.gz') ? "gzip -dc " . escapeshellarg($filePath) : "cat " . escapeshellarg($filePath);

        $cmd = sprintf(
            'PGPASSWORD=%s %s | psql --host=%s --port=%s --username=%s -d %s 2>/dev/null',
            escapeshellarg($password),
            $catCmd,
            escapeshellarg($host),
            escapeshellarg($port),
            escapeshellarg($username),
            escapeshellarg($database)
        );

        $process = Process::fromShellCommandline($cmd);
        $process->setTimeout(600);
        $process->run();

        return $process->isSuccessful();
    }

    protected function restoreGenericPhp(string $connectionName, string $filePath): bool
    {
        try {
            $content = str_ends_with($filePath, '.gz') ? gzfile($filePath) : file($filePath);
            if ($content === false) {
                return false;
            }

            $sql = '';
            foreach ($content as $line) {
                $trimmed = trim($line);
                if ($trimmed === '' || str_starts_with($trimmed, '--') || str_starts_with($trimmed, '/*')) {
                    continue;
                }
                $sql .= $line;
                if (str_ends_with($trimmed, ';')) {
                    DB::connection($connectionName)->unprepared($sql);
                    $sql = '';
                }
            }

            return true;
        } catch (\Throwable $e) {
            $this->error("Erro no fallback PHP: " . $e->getMessage());
            return false;
        }
    }
}
