"""
FastAPI - Porteiro do Data Lakehouse
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.models import VideoData, IngestResponse, ProcessResponse
from config.settings import API_KEY, LANDING_ZONE

app = FastAPI(
    title="Full Data Lakehouse API",
    description="API para ingestão de dados no Data Lakehouse",
    version="1.0.0"
)

security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica se a API key é válida"""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401, 
            detail="API key inválida"
        )
    return credentials.credentials


@app.get("/")
async def root():
    """Endpoint de health check"""
    return {
        "message": "Delta Lakehouse API está funcionando!",
        "timestamp": datetime.now(),
        "status": "healthy"
    }


@app.post("/api/ingest/video", response_model=IngestResponse)
async def ingest_video(
    video_data: VideoData,
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint para ingestão de dados de vídeo
    
    Este endpoint:
    1. Valida os dados usando Pydantic
    2. Salva o JSON na landing zone
    3. Retorna confirmação de recebimento
    """
    try:
        # Gera um nome único para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"video_{timestamp}_{unique_id}.json"
        filepath = LANDING_ZONE / filename
        
        # Adiciona metadados de ingestão
        data_with_metadata = {
            "data": video_data.dict(),
            "metadata": {
                "ingested_at": datetime.now().isoformat(),
                "source": "api_ingestion",
                "filename": filename
            }
        }
        
        # Salva o arquivo na landing zone
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_with_metadata, f, indent=2, ensure_ascii=False)
        
        return IngestResponse(
            status="success",
            message="Dados recebidos e salvos na landing zone",
            filename=filename,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@app.post("/api/ingest/videos/batch", response_model=IngestResponse)
async def ingest_videos_batch(
    videos_data: List[VideoData],
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint para ingestão em lote de múltiplos vídeos
    """
    try:
        # Gera um nome único para o arquivo de lote
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"videos_batch_{timestamp}_{unique_id}.json"
        filepath = LANDING_ZONE / filename
        
        # Converte todos os vídeos para dict
        videos_dict = [video.dict() for video in videos_data]
        
        # Adiciona metadados de ingestão
        data_with_metadata = {
            "data": videos_dict,
            "metadata": {
                "ingested_at": datetime.now().isoformat(),
                "source": "api_batch_ingestion",
                "filename": filename,
                "record_count": len(videos_dict)
            }
        }
        
        # Salva o arquivo na landing zone
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_with_metadata, f, indent=2, ensure_ascii=False)
        
        return IngestResponse(
            status="success",
            message=f"Lote de {len(videos_dict)} vídeos recebido e salvo na landing zone",
            filename=filename,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@app.get("/api/status")
async def get_status():
    """Endpoint para verificar o status do sistema"""
    try:
        # Conta arquivos na landing zone
        landing_files = list(LANDING_ZONE.glob("*.json"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "landing_zone": {
                "path": str(LANDING_ZONE),
                "pending_files": len(landing_files),
                "files": [f.name for f in landing_files[-5:]]  # Últimos 5 arquivos
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now(),
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    from config.settings import API_HOST, API_PORT
    
    print(f"🚀 Iniciando FastAPI em {API_HOST}:{API_PORT}")
    print(f"📁 Landing Zone: {LANDING_ZONE}")
    print(f"🔑 API Key: {API_KEY}")
    
    uvicorn.run(app, host=API_HOST, port=API_PORT) 