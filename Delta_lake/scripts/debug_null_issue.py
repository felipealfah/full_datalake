#!/usr/bin/env python3
"""
Script para debuggar o problema de tipos Null
"""
import sys
from pathlib import Path
import polars as pl

# Adiciona o diretório pai ao Python path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import LANDING_ZONE

def debug_file(file_path: Path):
    """Debug de um arquivo específico"""
    print(f"\n🔍 Debugando: {file_path.name}")
    print("=" * 50)
    
    try:
        # Lê o arquivo
        if file_path.suffix.lower() == '.csv':
            # Testa separadores comuns
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pl.read_csv(str(file_path), separator=sep, encoding="utf8-lossy", ignore_errors=True)
                    if df.height > 0:
                        print(f"✅ CSV lido com separador '{sep}'")
                        break
                except:
                    continue
            else:
                raise Exception("Nenhum separador funcionou")
        else:
            df = pl.read_excel(str(file_path))
        
        print(f"📊 Shape: {df.height} linhas, {df.width} colunas")
        print(f"📋 Schema:")
        
        # Analisa cada coluna
        null_cols = []
        for col in df.columns:
            dtype = df[col].dtype
            print(f"  {col}: {dtype}")
            if dtype == pl.Null:
                null_cols.append(col)
        
        print(f"\n❌ Colunas Null: {len(null_cols)}")
        if null_cols:
            print(f"   {null_cols}")
        
        # Testa conversão
        if null_cols:
            print(f"\n🔧 Testando conversão...")
            df_fixed = df.cast({col: pl.Utf8 for col in null_cols})
            print(f"✅ Conversão OK!")
            
            # Testa conversão para pandas
            pandas_df = df_fixed.to_pandas()
            print(f"✅ Pandas conversion OK!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    # Testa um arquivo problemático do renda_extra
    problema_file = LANDING_ZONE / "data" / "raw" / "renda_extra" / "Ticto.csv"
    debug_file(problema_file)
    
    # Testa um arquivo que funciona
    sucesso_file = LANDING_ZONE / "data" / "raw" / "diabetes" / "Sugar Defender Customers (1).xlsx"
    debug_file(sucesso_file)