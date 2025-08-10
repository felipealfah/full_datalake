#!/usr/bin/env python3
"""
Teste de processamento de um único arquivo
"""
import sys
import asyncio
from pathlib import Path

# Adiciona o diretório pai ao Python path
sys.path.append(str(Path(__file__).parent.parent))

from processamento.data_processor import DataProcessor
from config.settings import LANDING_ZONE

async def test_single_file():
    """Testa processamento de um arquivo problemático"""
    
    # Arquivo que está falhando
    problem_file = LANDING_ZONE / "data" / "raw" / "renda_extra" / "Ticto.csv"
    
    print(f"🧪 Testando: {problem_file.name}")
    print("=" * 50)
    
    processor = DataProcessor()
    
    try:
        await processor.process_file(problem_file, "renda_extra")
        print("✅ Sucesso!")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_file())