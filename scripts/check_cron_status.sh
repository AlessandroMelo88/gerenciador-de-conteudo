#!/bin/bash
# ==============================================================================
# Script: check_cron_status.sh
# Objetivo: Exibir de forma rápida e clara o status da retomada da sessão
# ==============================================================================

PROJECT_DIR="/Users/alessandrobm1/develop/server/wordpress/canaldecortes"
LOG_FILE="$PROJECT_DIR/scripts/resume_claude_session.log"
DAEMON_LOG="$PROJECT_DIR/scripts/daemon_runner.log"
CRON_LOG="$PROJECT_DIR/scripts/cron.log"
STATUS_JSON="$PROJECT_DIR/scripts/cron_status.json"

echo "================================================================"
echo "          STATUS DA RETOMADA DA SESSÃO CLAUDE CODE"
echo "================================================================"
echo "Hora atual: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Processos em execução
echo "--- Processos Ativos (Daemon / Caffeinate) ---"
PS_OUT=$(ps aux | grep -E "resume_claude|caffeinate" | grep -v grep)
if [ -n "$PS_OUT" ]; then
    echo "$PS_OUT"
else
    echo "Nenhum daemon/caffeinate rodando no momento."
fi
echo ""

# 2. Status no crontab
echo "--- Configuração no Crontab ---"
crontab -l 2>/dev/null | grep resume_claude || echo "Não encontrado no crontab."
echo ""

# 3. Status no launchctl (LaunchAgent)
echo "--- Status no LaunchAgent (launchd) ---"
launchctl list 2>/dev/null | grep canaldecortes || echo "Não encontrado no launchctl."
echo ""

# 4. Status estruturado (JSON)
if [ -f "$STATUS_JSON" ]; then
    echo "--- Último Status Registrado (JSON) ---"
    cat "$STATUS_JSON"
    echo ""
fi

# 5. Últimas linhas dos logs
echo "--- Últimas 15 linhas de resume_claude_session.log ---"
if [ -f "$LOG_FILE" ]; then
    tail -n 15 "$LOG_FILE"
else
    echo "(Arquivo de log ainda não criado ou sem registros)"
fi
echo ""

echo "--- Últimas 10 linhas de daemon_runner.log ---"
if [ -f "$DAEMON_LOG" ]; then
    tail -n 10 "$DAEMON_LOG"
fi
echo ""

echo "--- Branch Git Atual e Branches Disponíveis ---"
git -C "$PROJECT_DIR" branch -v
echo "================================================================"
