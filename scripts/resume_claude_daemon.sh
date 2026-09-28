#!/bin/bash
# ==============================================================================
# Script: resume_claude_daemon.sh
# Objetivo: Aguardar até as 03:21 AM mantendo a máquina acordada (caffeinate)
#           e disparar o script de retomada da sessão.
# ==============================================================================

set -u

PROJECT_DIR="/Users/alessandrobm1/develop/server/wordpress/canaldecortes"
SCRIPT_RESUME="$PROJECT_DIR/scripts/resume_claude_session.sh"
DAEMON_LOG="$PROJECT_DIR/scripts/daemon_runner.log"

cd "$PROJECT_DIR" || exit 1

log_daemon() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$DAEMON_LOG"
}

log_daemon "Daemon de monitoramento iniciado. Calculando horário alvo (03:21 AM)..."

TARGET_HOUR=3
TARGET_MIN=21

NOW_SEC=$(date '+%s')
TARGET_SEC=$(date -v${TARGET_HOUR}H -v${TARGET_MIN}M -v0S '+%s' 2>/dev/null || date -d "${TARGET_HOUR}:${TARGET_MIN}:00" '+%s' 2>/dev/null)

# Se o horário alvo já passou hoje (ex: agora é depois das 03:21 AM), e ainda é antes das 04:00 AM, roda logo.
# Se já passou das 04:00 AM, seria para o dia seguinte, mas como o limite reseta às 03:20 AM de hoje:
DIFF=$(( TARGET_SEC - NOW_SEC ))

if [ $DIFF -gt 0 ]; then
    log_daemon "Aguardando $DIFF segundos até as 03:21 AM..."
    sleep $DIFF
else
    log_daemon "Horário alvo já atingido ou ultrapassado ($DIFF seg). Disparando retomada imediatamente."
fi

log_daemon "Executando script de retomada: $SCRIPT_RESUME"
/bin/bash "$SCRIPT_RESUME" >> "$DAEMON_LOG" 2>&1
EXIT_CODE=$?

log_daemon "Script de retomada finalizou com código $EXIT_CODE."
exit $EXIT_CODE
