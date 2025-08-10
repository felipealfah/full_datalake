"""
File System Watcher para monitorar Landing Zone
Detecta novos arquivos Excel/CSV e triggera processamento
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config.settings import LANDING_ZONE
from processamento.data_processor import DataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LandingZoneHandler(FileSystemEventHandler):
    """Handler para eventos do sistema de arquivos na Landing Zone"""
    
    def __init__(self, data_processor: DataProcessor):
        super().__init__()
        self.data_processor = data_processor
        self.processing_files: Set[str] = set()
        self.supported_extensions = {'.xlsx', '.xls', '.csv'}
    
    def on_created(self, event):
        """Triggered quando um novo arquivo é criado"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Verifica se é um arquivo suportado
        if file_path.suffix.lower() not in self.supported_extensions:
            logger.info(f"Arquivo ignorado (formato não suportado): {file_path.name}")
            return
            
        # Evita processar o mesmo arquivo múltiplas vezes
        if str(file_path) in self.processing_files:
            return
            
        self.processing_files.add(str(file_path))
        
        # Detecta cluster pelo diretório pai
        cluster = self._detect_cluster(file_path)
        
        logger.info(f"📁 Novo arquivo detectado: {file_path.name} (cluster: {cluster})")
        
        # Agenda processamento assíncrono
        asyncio.create_task(self._process_file_async(file_path, cluster))
    
    def _detect_cluster(self, file_path: Path) -> str:
        """Detecta o cluster baseado no diretório pai"""
        try:
            # Caminho relativo à Landing Zone
            relative_path = file_path.relative_to(LANDING_ZONE / "data" / "raw")
            cluster = relative_path.parts[0] if relative_path.parts else "unknown"
            return cluster
        except ValueError:
            return "unknown"
    
    async def _process_file_async(self, file_path: Path, cluster: str):
        """Processa arquivo de forma assíncrona"""
        try:
            # Aguarda um pouco para garantir que o arquivo foi totalmente escrito
            await asyncio.sleep(1)
            
            logger.info(f"🔄 Iniciando processamento: {file_path.name}")
            
            # Chama o processador de dados
            await self.data_processor.process_file(file_path, cluster)
            
            logger.info(f"✅ Processamento concluído: {file_path.name}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {file_path.name}: {str(e)}")
        finally:
            # Remove da lista de processamento
            self.processing_files.discard(str(file_path))


class FileWatcher:
    """Watcher principal para monitorar a Landing Zone"""
    
    def __init__(self):
        self.observer = Observer()
        self.data_processor = DataProcessor()
        self.handler = LandingZoneHandler(self.data_processor)
        
        # Diretórios a monitorar
        self.watch_directories = [
            LANDING_ZONE / "data" / "raw" / "diabetes",
            LANDING_ZONE / "data" / "raw" / "emagrecimento", 
            LANDING_ZONE / "data" / "raw" / "rejuvenescimento",
            LANDING_ZONE / "data" / "raw" / "relacionamento",
            LANDING_ZONE / "data" / "raw" / "renda_extra"
        ]
    
    def start(self):
        """Inicia o monitoramento dos diretórios"""
        logger.info("🚀 Iniciando File System Watcher...")
        
        # Configura watchers para cada cluster
        for directory in self.watch_directories:
            if directory.exists():
                self.observer.schedule(self.handler, str(directory), recursive=False)
                logger.info(f"👀 Monitorando: {directory.name}/")
            else:
                logger.warning(f"⚠️  Diretório não encontrado: {directory}")
        
        self.observer.start()
        logger.info("✅ File System Watcher ativo!")
        
        try:
            self.observer.join()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Para o monitoramento"""
        logger.info("🛑 Parando File System Watcher...")
        self.observer.stop()
        self.observer.join()
        logger.info("✅ File System Watcher parado!")


async def scan_existing_files():
    """Processa arquivos que já existem na Landing Zone"""
    logger.info("🔍 Escaneando arquivos existentes na Landing Zone...")
    
    data_processor = DataProcessor()
    processed_count = 0
    
    for cluster_dir in [
        LANDING_ZONE / "data" / "raw" / "diabetes",
        LANDING_ZONE / "data" / "raw" / "emagrecimento",
        LANDING_ZONE / "data" / "raw" / "rejuvenescimento", 
        LANDING_ZONE / "data" / "raw" / "relacionamento",
        LANDING_ZONE / "data" / "raw" / "renda_extra"
    ]:
        if not cluster_dir.exists():
            continue
            
        cluster = cluster_dir.name
        
        # Processa todos os arquivos existentes
        for file_path in cluster_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in {'.xlsx', '.xls', '.csv'}:
                try:
                    logger.info(f"📄 Processando existente: {file_path.name} (cluster: {cluster})")
                    await data_processor.process_file(file_path, cluster)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"❌ Erro ao processar {file_path.name}: {str(e)}")
    
    logger.info(f"✅ Scan concluído! {processed_count} arquivos processados.")


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Processa arquivos existentes primeiro
        await scan_existing_files()
        
        # Inicia monitoramento contínuo
        watcher = FileWatcher()
        watcher.start()
    
    asyncio.run(main())