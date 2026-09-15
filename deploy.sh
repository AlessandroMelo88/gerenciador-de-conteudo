#!/usr/bin/env bash
# ==============================================================================
# CANAL DE CORTES - ULTRA-FAST DEPLOY SCRIPT
# ==============================================================================
# Executa deploy em ~10 a 20 segundos:
# 1. Compila Vite localmente (opcional com --skip-vite)
# 2. Sincroniza painel, branding e Python clip-processor via Rsync
# 3. Recarrega os containers Docker sem rebuild (graças aos volumes mapeados)
# 4. Limpa caches do Laravel e roda migrations
#
# Uso:
#   ./deploy.sh                # Deploy padrão rápido (~15s)
#   ./deploy.sh --skip-vite    # Se mexeu só no backend (~8s)
#   ./deploy.sh --build-docker # Apenas se mudar dependências de sistema (apt/pip)
# ==============================================================================

set -eo pipefail

SERVER_IP="147.15.124.191"
SERVER_USER="ubuntu"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/oracle-ssh-key-2026-08-27.key}"
REMOTE_DIR="/home/ubuntu/canaldecortes"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cores
CLR_GREEN="\033[1;32m"
CLR_BLUE="\033[1;34m"
CLR_YELLOW="\033[1;33m"
CLR_RED="\033[1;31m"
CLR_RESET="\033[0m"

echo -e "${CLR_BLUE}====================================================${CLR_RESET}"
echo -e "${CLR_BLUE}        🚀 CANAL DE CORTES - DEPLOY RÁPIDO          ${CLR_RESET}"
echo -e "${CLR_BLUE}====================================================${CLR_RESET}"
START_TIME=$(date +%s)

BUILD_DOCKER=false
SKIP_VITE=false

for arg in "$@"; do
    case $arg in
        --build-docker)
            BUILD_DOCKER=true
            ;;
        --skip-vite)
            SKIP_VITE=true
            ;;
        --help|-h)
            echo "Uso: ./deploy.sh [opções]"
            echo "Opções:"
            echo "  --skip-vite      Pula o build local do frontend (Vite)"
            echo "  --build-docker   Reconstrói a imagem Docker no servidor (demorado, usar só se mudar apt/pip)"
            exit 0
            ;;
    esac
done

# 1. Checar chave SSH
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${CLR_RED}❌ Chave SSH não encontrada em: $SSH_KEY${CLR_RESET}"
    exit 1
fi

# 2. Compilar frontend Vite se necessário
if [ "$SKIP_VITE" = false ]; then
    echo -e "\n${CLR_YELLOW}[1/4] Compilando frontend localmente (npm run build)...${CLR_RESET}"
    (cd "$PROJECT_DIR/painel" && npm run build)
else
    echo -e "\n${CLR_YELLOW}[1/4] Pulando build do frontend (--skip-vite ativo)...${CLR_RESET}"
fi

# 3. Sincronização Rsync ultrarrápida
echo -e "\n${CLR_YELLOW}[2/4] Sincronizando arquivos com o servidor de produção...${CLR_RESET}"

# Painel PHP/Laravel
rsync -rlzOv --delete \
    --no-perms --no-owner --no-group \
    --exclude 'node_modules' \
    --exclude '.env' \
    --exclude '.git' \
    --exclude 'storage' \
    --exclude 'bootstrap/cache' \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    "$PROJECT_DIR/painel/" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/painel/"

# Código Python do clip-processor
rsync -rlzOv --delete \
    --no-perms --no-owner --no-group \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    "$PROJECT_DIR/clip-processor/src/" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/clip-processor/src/"

# Branding e assets visuais
rsync -rlzOv \
    --no-perms --no-owner --no-group \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    "$PROJECT_DIR/branding/" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/branding/"

# Docker Compose e Dockerfile
rsync -rlzOv \
    --no-perms --no-owner --no-group \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    "$PROJECT_DIR/docker-compose.yml" \
    "$PROJECT_DIR/Dockerfile.php" \
    "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

# 4. Comandos no servidor
echo -e "\n${CLR_YELLOW}[3/4] Aplicando atualizações no servidor...${CLR_RESET}"

if [ "$BUILD_DOCKER" = true ]; then
    echo -e "${CLR_YELLOW}⚠️  Aviso: Rebuild do Docker solicitado (--build-docker)...${CLR_RESET}"
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
        cd /home/ubuntu/canaldecortes
        docker compose build clip-processor
        docker compose up -d
EOF
else
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
        cd /home/ubuntu/canaldecortes
        
        # Garante containers ativos com os volumes corretos
        docker compose up -d --no-recreate
        
        # Reinicia o clip-processor para carregar novo código Python instantaneamente (1s)
        docker compose restart clip-processor
        
        # Limpa caches e roda migrations no container PHP
        docker compose exec -T php php /var/www/html/painel/artisan optimize:clear
        docker compose exec -T php php /var/www/html/painel/artisan migrate --force
        
        # Reinicia o PHP-FPM para zerar opcache (1s)
        docker compose restart php
EOF
fi

echo -e "\n${CLR_YELLOW}[4/4] Verificando status dos containers...${CLR_RESET}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "\n${CLR_GREEN}====================================================${CLR_RESET}"
echo -e "${CLR_GREEN}   ✅ DEPLOY CONCLUÍDO COM SUCESSO EM ${DURATION}s!       ${CLR_RESET}"
echo -e "${CLR_GREEN}   Painel: https://toolscut.alessandromelo.com.br    ${CLR_RESET}"
echo -e "${CLR_GREEN}====================================================${CLR_RESET}"
