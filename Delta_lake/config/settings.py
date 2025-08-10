"""
Configurações do projeto Delta Lake
"""
import os
from pathlib import Path

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent

# Configurações da API
API_HOST = "0.0.0.0"
API_PORT = 8000
API_KEY = "seu_api_key_secreto_aqui"  # Mude isso em produção!

# Configurações Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Configure via variável de ambiente
GEMINI_MODEL = "gemini-1.5-flash"  # ou gemini-1.5-pro para tarefas mais complexas
GEMINI_TIMEOUT = 30  # segundos

# Configurações de Dados
DATA_ROOT = PROJECT_ROOT / "dados"
LANDING_ZONE = PROJECT_ROOT.parent / "Landing_zone"
BRONZE_PATH = DATA_ROOT / "bronze"
SILVER_PATH = DATA_ROOT / "silver"
GOLD_PATH = DATA_ROOT / "gold"

# Garante que os diretórios existem
for path in [DATA_ROOT, LANDING_ZONE, BRONZE_PATH, SILVER_PATH, GOLD_PATH]:
    path.mkdir(exist_ok=True, parents=True)

