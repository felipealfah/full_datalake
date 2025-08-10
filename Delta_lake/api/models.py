"""
Modelos Pydantic para validação de dados
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class IngestResponse(BaseModel):
    """Resposta da API de ingestão"""
    status: str
    message: str
    filename: Optional[str] = None
    timestamp: datetime


class ProcessResponse(BaseModel):
    """Resposta da API de processamento"""
    status: str
    message: str
    records_processed: Optional[int] = None
    timestamp: datetime 