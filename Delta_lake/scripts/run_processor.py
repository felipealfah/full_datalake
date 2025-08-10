#!/usr/bin/env python3
"""
Script para testar o processamento de dados
Roda o file watcher e processa arquivos existentes
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório pai ao Python path
sys.path.append(str(Path(__file__).parent.parent))

from processamento.file_watcher import FileWatcher, scan_existing_files


async def main():
    """Função principal"""
    print("🚀 Iniciando processamento de dados...")
    print("=" * 50)
    
    try:
        # 1. Processa arquivos existentes
        print("\n🔍 Fase 1: Processando arquivos existentes...")
        await scan_existing_files()
        
        print("\n✅ Arquivos existentes processados!")
        print("\n👀 Fase 2: Iniciando monitoramento contínuo...")
        print("   (Pressione Ctrl+C para parar)")
        
        # 2. Inicia monitoramento contínuo
        watcher = FileWatcher()
        watcher.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Processamento interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())