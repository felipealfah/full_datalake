"""
Data Processor - Lê Excel/CSV e escreve para Delta Lake
Suporta múltiplos formatos e schema evolution
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import polars as pl
from deltalake import write_deltalake, DeltaTable

from config.settings import BRONZE_PATH, SILVER_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Processador principal para arquivos Excel/CSV → Delta Lake"""
    
    def __init__(self):
        self.supported_formats = {
            '.xlsx': self._read_excel,
            '.xls': self._read_excel,
            '.csv': self._read_csv
        }
    
    async def process_file(self, file_path: Path, cluster: str):
        """
        Processa um arquivo e salva no Bronze layer
        
        Args:
            file_path: Caminho para o arquivo
            cluster: Nome do cluster (diabetes, emagrecimento, etc.)
        """
        try:
            logger.info(f"📊 Lendo arquivo: {file_path.name}")
            
            # Lê o arquivo baseado na extensão
            df = await self._read_file(file_path)
            
            if df is None or df.height == 0:
                logger.warning(f"⚠️  Arquivo vazio ou inválido: {file_path.name}")
                return
            
            # Adiciona metadados
            df_with_metadata = self._add_metadata(df, file_path, cluster)
            
            # Salva no Bronze layer
            await self._save_to_bronze(df_with_metadata, cluster, file_path.stem)
            
            logger.info(f"✅ Arquivo salvo no Bronze: {file_path.name} ({df.height} registros)")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {file_path.name}: {str(e)}")
            raise
    
    async def _read_file(self, file_path: Path) -> Optional[pl.DataFrame]:
        """Lê arquivo baseado na extensão"""
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_formats:
            raise ValueError(f"Formato não suportado: {extension}")
        
        try:
            return self.supported_formats[extension](file_path)
        except Exception as e:
            logger.error(f"Erro ao ler {file_path.name}: {str(e)}")
            return None
    
    def _read_excel(self, file_path: Path) -> pl.DataFrame:
        """Lê arquivos Excel (.xlsx, .xls)"""
        try:
            # Tenta ler com Polars primeiro (mais rápido)
            df = pl.read_excel(str(file_path))
            logger.info(f"📈 Excel lido: {df.height} linhas, {df.width} colunas")
            return df
        except Exception as e:
            logger.warning(f"Polars falhou, tentando pandas: {str(e)}")
            # Fallback para pandas se Polars falhar
            import pandas as pd
            pdf = pd.read_excel(str(file_path))
            df = pl.from_pandas(pdf)
            logger.info(f"📈 Excel lido (pandas): {df.height} linhas, {df.width} colunas")
            return df
    
    def _read_csv(self, file_path: Path) -> pl.DataFrame:
        """Lê arquivos CSV com detecção automática de separador"""
        try:
            # Fallback com separadores comuns (mais robusto)
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pl.read_csv(
                        str(file_path), 
                        separator=sep, 
                        encoding="utf8-lossy",
                        ignore_errors=True,
                        infer_schema_length=1000  # Melhor inferência de tipos
                    )
                    if df.height > 0:  # Verifica se leu dados
                        logger.info(f"📈 CSV lido (sep '{sep}'): {df.height} linhas, {df.width} colunas")
                        return df
                except Exception as e:
                    continue
            
            # Se todos falharem, tenta como pandas fallback
            import pandas as pd
            pdf = pd.read_csv(str(file_path), encoding='utf-8', on_bad_lines='skip')
            df = pl.from_pandas(pdf)
            logger.info(f"📈 CSV lido (pandas fallback): {df.height} linhas, {df.width} colunas")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler CSV {file_path.name}: {str(e)}")
            raise e
    
    def _add_metadata(self, df: pl.DataFrame, file_path: Path, cluster: str) -> pl.DataFrame:
        """Adiciona colunas de metadados ao DataFrame"""
        # Converte colunas Null para String para compatibilidade Delta Lake
        df_clean = self._clean_null_columns(df)
        
        return df_clean.with_columns([
            pl.lit(file_path.name).alias("_source_file"),
            pl.lit(cluster).alias("_cluster"),
            pl.lit(datetime.now().isoformat()).alias("_ingested_at"),
            pl.lit(file_path.stat().st_size).alias("_file_size_bytes"),
            pl.lit(df.height).alias("_row_count")
        ])
    
    def _clean_null_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Limpa colunas com tipos Null para compatibilidade Delta Lake"""
        try:
            # Força conversão de todas as colunas Null para String
            cast_dict = {}
            null_count = 0
            
            for col in df.columns:
                dtype = df[col].dtype
                if dtype == pl.Null:
                    cast_dict[col] = pl.Utf8
                    null_count += 1
                elif str(dtype).startswith('List') or str(dtype).startswith('Struct'):
                    # Converte tipos complexos para string também
                    cast_dict[col] = pl.Utf8
                    null_count += 1
            
            if cast_dict:
                logger.warning(f"🔧 Convertendo {null_count} colunas problemáticas para String")
                df = df.cast(cast_dict)
            
            # Fallback adicional: garante que não há tipos incompatíveis
            pandas_df = df.to_pandas()
            
            # Remove colunas completamente vazias do pandas
            pandas_df = pandas_df.dropna(axis=1, how='all')
            
            # Preenche valores NaN com strings vazias
            pandas_df = pandas_df.fillna('')
            
            # Converte de volta para Polars
            df_clean = pl.from_pandas(pandas_df)
            
            logger.info(f"✅ DataFrame limpo: {df_clean.height} linhas, {df_clean.width} colunas")
            return df_clean
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar DataFrame: {str(e)}")
            # Last resort: converte tudo para string
            try:
                pandas_df = df.to_pandas()
                # Converte todas as colunas para string
                for col in pandas_df.columns:
                    pandas_df[col] = pandas_df[col].astype(str).fillna('')
                
                df_final = pl.from_pandas(pandas_df)
                logger.warning(f"⚠️  Fallback aplicado: todas colunas convertidas para string")
                return df_final
            except Exception as final_e:
                logger.error(f"❌ Fallback final falhou: {str(final_e)}")
                raise final_e
    
    async def _save_to_bronze(self, df: pl.DataFrame, cluster: str, file_stem: str):
        """Salva DataFrame no Bronze layer como tabela Delta"""
        
        # Caminho da tabela Bronze por cluster
        table_path = BRONZE_PATH / f"{cluster}_bronze"
        
        # Converte Polars para formato compatível com Delta Lake
        pandas_df = df.to_pandas()
        
        try:
            # Verifica se tabela já existe
            if table_path.exists():
                # Append mode - adiciona novos dados
                write_deltalake(
                    str(table_path),
                    pandas_df,
                    mode="append",
                    schema_mode="merge"  # Permite evolução do schema
                )
                logger.info(f"📊 Dados adicionados à tabela existente: {cluster}_bronze")
            else:
                # Create mode - primeira vez
                table_path.mkdir(parents=True, exist_ok=True)
                write_deltalake(
                    str(table_path),
                    pandas_df,
                    mode="overwrite"
                )
                logger.info(f"🆕 Nova tabela Delta criada: {cluster}_bronze")
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar no Delta Lake: {str(e)}")
            raise
    
    def get_bronze_table_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das tabelas Bronze"""
        stats = {}
        
        for cluster_dir in BRONZE_PATH.iterdir():
            if cluster_dir.is_dir() and cluster_dir.name.endswith("_bronze"):
                try:
                    table = DeltaTable(str(cluster_dir))
                    df = table.to_pandas()
                    
                    cluster_name = cluster_dir.name.replace("_bronze", "")
                    stats[cluster_name] = {
                        "rows": len(df),
                        "columns": len(df.columns),
                        "last_modified": cluster_dir.stat().st_mtime,
                        "size_mb": sum(f.stat().st_size for f in cluster_dir.rglob("*") if f.is_file()) / 1024 / 1024
                    }
                except Exception as e:
                    logger.warning(f"Erro ao ler stats de {cluster_dir.name}: {str(e)}")
        
        return stats


if __name__ == "__main__":
    # Teste do processador
    processor = DataProcessor()
    
    # Lista arquivos para processar
    raw_path = LANDING_ZONE / "data" / "raw"
    
    for cluster_dir in raw_path.iterdir():
        if cluster_dir.is_dir():
            print(f"\n📁 Cluster: {cluster_dir.name}")
            for file_path in cluster_dir.iterdir():
                if file_path.suffix.lower() in {'.xlsx', '.xls', '.csv'}:
                    print(f"  📄 {file_path.name}")