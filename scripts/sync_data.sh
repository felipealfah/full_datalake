#!/bin/bash
set -e

# Configurações da VPS
VPS_HOST="your-vps-ip"
VPS_USER="delta-user"
VPS_PATH="/opt/delta-lake"

echo "📊 Sincronização de Dados - Delta Lake"
echo "======================================"

# Função para log com timestamp
log() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# Verifica conexão SSH
if ! ssh -o ConnectTimeout=5 $VPS_USER@$VPS_HOST "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "❌ Erro: Não foi possível conectar via SSH"
    exit 1
fi

# OPÇÃO 1: Sync Landing Zone (arquivos originais)
if [ "$1" = "landing" ] || [ "$1" = "all" ]; then
    log "📁 Sincronizando Landing Zone..."
    
    # Cria estrutura de diretórios
    ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_PATH/Landing_zone/data/raw/{diabetes,emagrecimento,rejuvenescimento,relacionamento,renda_extra}"
    
    # Sync arquivos
    rsync -av --progress --stats \
        ./Landing_zone/data/raw/ \
        $VPS_USER@$VPS_HOST:$VPS_PATH/Landing_zone/data/raw/
    
    log "✅ Landing Zone sincronizada"
fi

# OPÇÃO 2: Sync tabelas Bronze (dados processados)
if [ "$1" = "bronze" ] || [ "$1" = "all" ]; then
    if [ -d "./Delta_lake/dados/bronze" ] && [ "$(ls -A ./Delta_lake/dados/bronze)" ]; then
        log "💾 Sincronizando tabelas Bronze..."
        
        # Cria diretório bronze na VPS
        ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_PATH/Delta_lake/dados/bronze"
        
        # Sync tabelas Delta
        rsync -av --progress --stats \
            ./Delta_lake/dados/bronze/ \
            $VPS_USER@$VPS_HOST:$VPS_PATH/Delta_lake/dados/bronze/
        
        log "✅ Tabelas Bronze sincronizadas"
    else
        log "ℹ️  Sem tabelas Bronze para sincronizar"
    fi
fi

# OPÇÃO 3: Download dados da VPS (backup)
if [ "$1" = "download" ]; then
    log "⬇️  Baixando dados da VPS..."
    
    # Backup Landing Zone
    rsync -av --progress \
        $VPS_USER@$VPS_HOST:$VPS_PATH/Landing_zone/data/raw/ \
        ./backup/landing_zone/
    
    # Backup Bronze tables
    rsync -av --progress \
        $VPS_USER@$VPS_HOST:$VPS_PATH/Delta_lake/dados/bronze/ \
        ./backup/bronze/
    
    log "✅ Backup concluído em ./backup/"
fi

# Status dos dados na VPS
log "📊 Status dos dados na VPS:"
ssh $VPS_USER@$VPS_HOST << EOF
    cd $VPS_PATH
    echo "Landing Zone:"
    find Landing_zone/data/raw -name "*.xlsx" -o -name "*.xls" -o -name "*.csv" | wc -l | xargs echo "  Arquivos:"
    
    echo "Bronze Tables:"
    ls -la Delta_lake/dados/bronze/ 2>/dev/null | grep '^d' | wc -l | xargs echo "  Tabelas:"
EOF

echo ""
echo "💡 Uso:"
echo "  ./sync_data.sh landing  # Sync apenas Landing Zone"
echo "  ./sync_data.sh bronze   # Sync apenas tabelas Bronze"
echo "  ./sync_data.sh all      # Sync tudo"
echo "  ./sync_data.sh download # Backup da VPS"