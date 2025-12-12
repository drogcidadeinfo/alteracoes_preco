# main.py
import pandas as pd
import time
from datetime import datetime

from config import *
from file_utils import limpar_pasta_arquivos, encontrar_arquivo_mais_recente, salvar_dataframe_csv, ler_excel_com_cabecalho
from scraper import TrierScraper
from etiquetas import gerar_etiquetas_por_filial
from email_sender import enviar_email_com_pdfs

def main():
    print("=" * 60)
    print("🚀 SISTEMA DE AUTOMAÇÃO - ALTERAÇÕES DE PREÇO")
    print("=" * 60)
    
    # Limpa pasta de arquivos
    print("\n🧹 Limpando pasta de arquivos...")
    limpar_pasta_arquivos()
    
    # Cria diretórios se não existirem
    os.makedirs(ARQUIVOS_DIR, exist_ok=True)
    
    scraper = None
    try:
        # === ETAPA 1: BAIXAR RELATÓRIOS ===
        print("\n" + "=" * 60)
        print("ETAPA 1: BAIXANDO RELATÓRIOS DO SISTEMA")
        print("=" * 60)
        
        scraper = TrierScraper()
        scraper.login()
        
        relatorio_pdf, arquivo_xls = scraper.baixar_relatorio_precos()
        
        # Processa o XLS baixado
        df = pd.read_excel(arquivo_xls, header=7)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            'Código': 'Código',
            'Descrição Produto': 'Produto',
            'Preço Venda Atual': 'Preço'
        }).dropna(subset=['Código'])
        
        print(f"\n✅ {len(df)} produtos encontrados no relatório.")
        
        if len(df) == 0:
            print("⚠️ Nenhum produto alterado encontrado. Encerrando...")
            return
        
        # === ETAPA 2: EXTRAIR EAN E DESCRIÇÃO ===
        print("\n" + "=" * 60)
        print("ETAPA 2: EXTRAINDO EAN E DESCRIÇÃO COMPLETA")
        print("=" * 60)
        
        eans, descricoes = scraper.extrair_dados_produtos(df)
        df['EAN'] = eans
        df['Descrição Completa'] = descricoes
        
        # Salva CSV completo
        arquivo_csv = salvar_dataframe_csv(df)
        
        # === ETAPA 3: BAIXAR RELATÓRIO DE ESTOQUE ===
        print("\n" + "=" * 60)
        print("ETAPA 3: BAIXANDO RELATÓRIO DE ESTOQUE")
        print("=" * 60)
        
        arquivo_estoque = scraper.baixar_relatorio_estoque(df['Código'])
        scraper.fechar()
        
        # Processa estoque
        df_estoque = ler_excel_com_cabecalho(arquivo_estoque)
        
        # === ETAPA 4: GERAR ETIQUETAS ===
        print("\n" + "=" * 60)
        print("ETAPA 4: GERANDO ETIQUETAS POR FILIAL")
        print("=" * 60)
        
        arquivos_etiquetas = gerar_etiquetas_por_filial(df, df_estoque, SAIDA_DIR)
        
        if not arquivos_etiquetas:
            print("⚠️ Nenhuma etiqueta foi gerada. Encerrando...")
            return
        
        # Convert etiquetas keys to strings to match email map
        arquivos_etiquetas_str = {str(k): v for k, v in arquivos_etiquetas.items()}
        
        # === ETAPA 5: ENVIAR EMAILS ===
        print("\n" + "=" * 60)
        print("ETAPA 5: ENVIANDO EMAILS")
        print("=" * 60)
        
        enviar_email_com_pdfs(relatorio_pdf, arquivos_etiquetas_str)
                
        print("\n" + "=" * 60)
        print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if scraper:
            scraper.fechar()

if __name__ == "__main__":
    main()
