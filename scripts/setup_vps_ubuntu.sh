#!/bin/bash
set -e

echo "🚀 Setup VPS Ubuntu 22.04 - Delta Lake Production"
echo "================================================="

# Função para log com timestamp
log() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# Atualiza sistema
log "📦 Atualizando sistema Ubuntu..."
sudo apt-get update && sudo apt-get upgrade -y

# Instala dependências essenciais
log "🔧 Instalando dependências do sistema..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    htop \
    rsync

# Instala Docker
log "🐳 Instalando Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adiciona usuário ao grupo docker
sudo usermod -aG docker $USER

# Instala Docker Compose standalone
log "🔨 Instalando Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Cria usuário delta-user
log "👤 Criando usuário delta-user..."
sudo useradd -m -s /bin/bash delta-user
sudo usermod -aG docker delta-user

# Cria diretório do projeto
log "📁 Criando estrutura de diretórios..."
sudo mkdir -p /opt/delta-lake
sudo chown delta-user:delta-user /opt/delta-lake

# Configura firewall
log "🔒 Configurando firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000  # API porta

# Instala Nginx (proxy reverso)
log "🌐 Instalando Nginx..."
sudo apt-get install -y nginx

# Configura Nginx para Delta Lake API
log "⚙️  Configurando Nginx..."
sudo tee /etc/nginx/sites-available/delta-lake << 'EOF'
server {
    listen 80;
    server_name _;  # Substitua pelo seu domínio

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Ativa site Nginx
sudo ln -sf /etc/nginx/sites-available/delta-lake /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Configura systemd para Docker Compose
log "⚙️  Configurando systemd service..."
sudo tee /etc/systemd/system/delta-lake.service << 'EOF'
[Unit]
Description=Delta Lake Data Lakehouse
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/delta-lake
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=delta-user
Group=delta-user

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable delta-lake

# Instala Python e uv (para desenvolvimento local na VPS se necessário)
log "🐍 Instalando Python e uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc

# Cria estrutura inicial como delta-user
log "📂 Criando estrutura inicial..."
sudo -u delta-user mkdir -p /opt/delta-lake/{Landing_zone/data/raw,Delta_lake/dados/{bronze,silver,gold},logs}

# Configura logrotate
log "📝 Configurando logrotate..."
sudo tee /etc/logrotate.d/delta-lake << 'EOF'
/opt/delta-lake/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 delta-user delta-user
    postrotate
        docker-compose -f /opt/delta-lake/docker-compose.prod.yml restart delta-processor
    endscript
}
EOF

log "✅ Setup VPS concluído!"

echo ""
echo "🎉 VPS Ubuntu configurada com sucesso!"
echo "======================================"
echo "👤 Usuário: delta-user"
echo "📁 Projeto: /opt/delta-lake"
echo "🐳 Docker: Instalado e configurado"
echo "🌐 Nginx: Configurado como proxy reverso"
echo "🔒 UFW: Firewall configurado"
echo "⚙️  Systemd: Serviço delta-lake criado"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure sua chave SSH: ssh-copy-id delta-user@VPS_IP"
echo "2. Edite scripts/deploy_hybrid.sh com IP da VPS"
echo "3. Execute: ./scripts/deploy_hybrid.sh"
echo ""
echo "🔄 Para reiniciar:"
echo "  sudo systemctl restart delta-lake"
echo "  docker-compose -f docker-compose.prod.yml logs -f"