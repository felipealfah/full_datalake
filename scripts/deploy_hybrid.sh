#!/bin/bash
set -e

# Configurações da VPS
VPS_HOST="your-vps-ip"
VPS_USER="delta-user"
VPS_PATH="/opt/delta-lake"

echo "🚀 Deploy Híbrido - Delta Lake Lakehouse"
echo "========================================"

# Verifica se SSH está configurado
if ! ssh -o ConnectTimeout=5 $VPS_USER@$VPS_HOST "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "❌ Erro: Não foi possível conectar via SSH"
    echo "Configure: ssh-keygen && ssh-copy-id $VPS_USER@$VPS_HOST"
    exit 1
fi

echo "✅ SSH conectado com sucesso"

# Função para log com timestamp
log() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# FASE 1: Deploy da aplicação via Git
log "📦 Fase 1: Deploy da aplicação..."

ssh $VPS_USER@$VPS_HOST << 'EOF'
    # Criar diretório se não existir
    sudo mkdir -p /opt/delta-lake
    sudo chown delta-user:delta-user /opt/delta-lake
    cd /opt/delta-lake
    
    # Clone/pull do repositório
    if [ -d ".git" ]; then
        echo "🔄 Atualizando repositório..."
        git pull origin main
    else
        echo "📥 Clonando repositório..."
        # Substitua pela URL do seu repositório
        git clone https://github.com/seu-usuario/delta-lakehouse.git .
    fi
    
    # Build dos containers
    echo "🐳 Building containers..."
    docker-compose -f docker-compose.prod.yml build
EOF

log "✅ Aplicação deployada"

# FASE 2: Sincronizar dados
log "📊 Fase 2: Sincronizando dados..."

# Criar estrutura de diretórios na VPS
ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_PATH/Landing_zone/data/raw/{diabetes,emagrecimento,rejuvenescimento,relacionamento,renda_extra}"

# Sync Landing Zone (arquivos originais)
log "📁 Sincronizando Landing Zone..."
rsync -av --progress \
    ./Landing_zone/data/raw/ \
    $VPS_USER@$VPS_HOST:$VPS_PATH/Landing_zone/data/raw/

# Sync tabelas Bronze (dados já processados)
if [ -d "./Delta_lake/dados/bronze" ] && [ "$(ls -A ./Delta_lake/dados/bronze)" ]; then
    log "💾 Sincronizando tabelas Bronze..."
    rsync -av --progress \
        ./Delta_lake/dados/bronze/ \
        $VPS_USER@$VPS_HOST:$VPS_PATH/Delta_lake/dados/bronze/
else
    log "ℹ️  Sem tabelas Bronze para sincronizar"
fi

log "✅ Dados sincronizados"

# FASE 3: Iniciar serviços
log "🚀 Fase 3: Iniciando serviços..."

ssh $VPS_USER@$VPS_HOST << 'EOF'
    cd /opt/delta-lake
    
    # Para serviços existentes
    docker-compose -f docker-compose.prod.yml down
    
    # Inicia serviços em background
    docker-compose -f docker-compose.prod.yml up -d
    
    # Aguarda inicialização
    sleep 10
    
    # Verifica status
    docker-compose -f docker-compose.prod.yml ps
EOF

log "✅ Deploy concluído!"

# FASE 4: Verificações finais
log "🔍 Verificações finais..."

# Testa API
if curl -f http://$VPS_HOST:8000/ > /dev/null 2>&1; then
    log "✅ API respondendo"
else
    log "⚠️  API não está respondendo"
fi

# Mostra logs
ssh $VPS_USER@$VPS_HOST "cd $VPS_PATH && docker-compose -f docker-compose.prod.yml logs --tail=10"

echo ""
echo "🎉 Deploy híbrido concluído!"
echo "📊 API: http://$VPS_HOST:8000"
echo "📁 Landing Zone: $VPS_PATH/Landing_zone/data/raw/"
echo "💾 Bronze Tables: $VPS_PATH/Delta_lake/dados/bronze/"
echo ""
echo "Para adicionar dados:"
echo "1. Clusters existentes: Apenas coloque arquivos nas pastas"
echo "2. Novos clusters: Crie pasta + reinicie container"