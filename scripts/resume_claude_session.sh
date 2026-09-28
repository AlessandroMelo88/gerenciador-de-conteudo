#!/bin/bash
# ==============================================================================
# Script: resume_claude_session.sh
# Objetivo: Retomar automaticamente a sessão do Claude Code interrompida pelo
#           limite de sessão às 03:20 AM (horário de Brasília).
# ==============================================================================

set -u

PROJECT_DIR="/Users/alessandrobm1/develop/server/wordpress/canaldecortes"
SESSION_ID="d30e2360-9c6a-4b69-888b-937c8701ae3d"
CLAUDE_BIN="/Users/alessandrobm1/.local/bin/claude"
LOG_FILE="$PROJECT_DIR/scripts/resume_claude_session.log"
LOCK_FILE="/tmp/resume_claude_canaldecortes.lock"
STATUS_FILE="$PROJECT_DIR/scripts/cron_status.json"

# Configurar variáveis de ambiente completas
export HOME="/Users/alessandrobm1"
export USER="alessandrobm1"
export PATH="/Users/alessandrobm1/.local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export SHELL="/bin/zsh"

cd "$PROJECT_DIR" || exit 1

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

update_status() {
    local status="$1"
    local detail="$2"
    cat <<EOF > "$STATUS_FILE"
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "local_time": "$(date '+%Y-%m-%d %H:%M:%S')",
  "status": "$status",
  "session_id": "$SESSION_ID",
  "detail": "$detail"
}
EOF
}

# Controle de lock para evitar execuções simultâneas (cron vs launchd vs daemon)
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        log "Execução abortada: outro processo ($PID) já está executando este job."
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

log "========================================================"
log "Iniciando verificação de retomada da sessão Claude Code"
log "Session ID: $SESSION_ID"
log "Diretório do projeto: $PROJECT_DIR"
log "========================================================"

update_status "STARTING" "Script iniciado e aguardando liberação do limite da API."

PROMPT_TEXT="O limite de sessão foi resetado. Por favor, continue exatamente a partir da instrução anterior: crie uma branch chamada 'afiliadas' a partir da branch 'main' e execute o desenvolvimento planejado para o sistema de afiliados conforme especificado no PLANO-MESTRE.md (Fase 6), implementando o schema no banco, models, rotas de API para ofertas e o worker de afiliados."

MAX_RETRIES=15
RETRY_DELAY=60
SUCCESS=false

for ((i=1; i<=MAX_RETRIES; i++)); do
    log "Tentativa $i/$MAX_RETRIES: testando status do limite..."
    
    # Faz uma chamada rápida para checar se o limite ainda está ativo
    CHECK_OUTPUT=$("$CLAUDE_BIN" -p -r "$SESSION_ID" "status_ping_check" < /dev/null 2>&1 || true)
    
    if echo "$CHECK_OUTPUT" | grep -qi "limit resets"; then
        log "Limite de sessão ainda ativo. Resposta: $(echo "$CHECK_OUTPUT" | head -n 2)"
        update_status "WAITING_LIMIT_RESET" "Tentativa $i/$MAX_RETRIES: Limite ainda ativo, aguardando $RETRY_DELAY segundos."
        
        if [ $i -lt $MAX_RETRIES ]; then
            log "Aguardando $RETRY_DELAY segundos antes de tentar novamente..."
            sleep $RETRY_DELAY
        fi
    else
        log "Limite de sessão LIBERADO! Iniciando execução do prompt na sessão..."
        update_status "RUNNING" "Limite liberado. Claude Code está processando a instrução na sessão."
        
        # Executar a continuação na sessão com permissões automáticas em background
        log "Executando claude com a instrução de continuação..."
        
        "$CLAUDE_BIN" -r "$SESSION_ID" --dangerously-skip-permissions -p "$PROMPT_TEXT" < /dev/null >> "$LOG_FILE" 2>&1
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            log "Claude Code concluiu a execução com SUCESSO (exit code 0)."
            update_status "COMPLETED_SUCCESS" "Sessão retomada e prompt processado com sucesso."
            SUCCESS=true
        else
            log "Claude Code finalizou com código de saída: $EXIT_CODE. Verifique os logs acima."
            update_status "COMPLETED_WITH_ERROR" "Claude Code encerrou com código $EXIT_CODE."
            SUCCESS=true
        fi
        break
    fi
done

if [ "$SUCCESS" = false ]; then
    log "ATENÇÃO: Atingido o número máximo de tentativas ($MAX_RETRIES) e o limite ainda não havia resetado."
    update_status "MAX_RETRIES_EXCEEDED" "Limite de sessão não resetou após $MAX_RETRIES tentativas."
    exit 1
fi

log "Job de retomada finalizado."
exit 0
