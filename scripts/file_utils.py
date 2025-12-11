# file_utils.py
import os
import glob
import shutil
from datetime import datetime
import pandas as pd
from config import ARQUIVOS_DIR

def limpar_pasta_arquivos():
    """Limpa todos os arquivos da pasta de arquivos"""
    for nome in os.listdir(ARQUIVOS_DIR):
        caminho = os.path.join(ARQUIVOS_DIR, nome)
        try:
            if os.path.isfile(caminho) or os.path.islink(caminho):
                os.remove(caminho)
            elif os.path.isdir(caminho):
                shutil.rmtree(caminho)
        except Exception as e:
            print(f"⚠️ Não foi possível remover {caminho}: {e}")

def encontrar_arquivo_mais_recente(extensao):
    """Encontra o arquivo mais recente com a extensão especificada"""
    arquivos = glob.glob(os.path.join(ARQUIVOS_DIR, f"*.{extensao}"))
    if not arquivos:
        return None
    return max(arquivos, key=os.path.getctime)

def salvar_dataframe_csv(df, prefixo="produtos_completos"):
    """Salva um DataFrame como CSV com timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    caminho = os.path.join(ARQUIVOS_DIR, f"{prefixo}_{timestamp}.csv")
    df.to_csv(caminho, index=False, sep=';', encoding='utf-8-sig')
    print(f"💾 Arquivo salvo: {caminho}")
    return caminho

def ler_excel_com_cabecalho(caminho, linha_cabecalho=11):
    """Lê arquivo Excel com cabeçalho em linha específica"""
    return pd.read_excel(caminho, header=linha_cabecalho)
