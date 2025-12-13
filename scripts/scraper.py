# scraper.py
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import glob
import os

from config import *
from file_utils import *

class TrierScraper:
    def __init__(self):
        self.navegador = None
        self.wait = None
        self.setup_navegador()
    
    def setup_navegador(self):
        """Configura o navegador Chrome"""
        chrome_options = webdriver.ChromeOptions()
        
        if CHROME_OPTIONS["headless"]:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--enable-downloads")  # Explicitly enable downloads
        chrome_options.add_argument(f"--window-size={CHROME_OPTIONS['window_size']}")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://drogcidade.ddns.net:4647/sgfpod1/Login.pod")
        
        prefs = {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True, # auto-downloads pdf files instead of opening in new window
            "download.open_pdf_in_system_reader": False,
            "pdfjs.disabled": True,  # Disable built-in PDF viewer
            "directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.navegador = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.navegador, 30)
    
    def login(self):
        """Realiza login no sistema"""
        print("➡️ Acessando o sistema...")
        self.navegador.get(LOGIN_URL)
        
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="id_cod_usuario"]'))).send_keys(LOGIN_USUARIO)
        print("✅ Usuário inserido.")
        
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="nom_senha"]'))).send_keys(LOGIN_SENHA)
        print("✅ Senha inserida.")
        
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login"]'))).click()
        print("🔐 Login realizado com sucesso.")
        
        time.sleep(3)
        self.navegador.find_element(By.TAG_NAME, "body").send_keys(Keys.F11)
        print("🪟 Tela maximizada (F11).")
    
    def baixar_relatorio_precos(self):
        """Baixa relatório de preços em PDF e XLS"""
        print("📂 Acessando menu de relatórios...")
        
        # Navegação até o relatório
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuBar"]/li[11]/a/span[2]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul123"]/li[7]/a/span'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul130"]/li[2]/a/span'))).click()
        
        # Configura departamento
        campo_departamento = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cod_deptoEntrada"]')))
        campo_departamento.send_keys('121')
        campo_departamento.send_keys(Keys.ENTER)
        self.wait.until(EC.invisibility_of_element_located((By.ID, 'divLoading')))
        time.sleep(0.5)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="consid_depto_D"]'))).click()
        
        # Acessa aba de filtros
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabTabdhtmlgoodies_tabView1_1"]/a'))).click()
        print("🧾 Aba de filtros acessada.")
        
        # Define período (ontem)
        data = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dat_init"]'))).send_keys("12/12/2025")
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dat_fim"]'))).send_keys("12/12/2025")
        print(f"📅 Período definido: {data} a {data}")
        
        # Configura filtros
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ultima_alteracao"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sel_produ_alt_3"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sel_tipo_alt_preco_2"]'))).click()
        
        # Baixa PDF
        print("📄 Gerando relatório em PDF...")
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="runReport"]'))).click()
        self.wait.until(EC.invisibility_of_element_located((By.ID, "divLoading")))
        time.sleep(6)
        
        # Aguarda download do PDF
        print("⏳ Aguardando download do PDF...")
        time.sleep(5)
        pdfs = glob.glob(os.path.join(DOWNLOAD_DIR, "*.pdf"))
        if pdfs:
            pdf_recente = max(pdfs, key=os.path.getctime)
            print(f"💾 PDF baixado com sucesso: {pdf_recente}")
            relatorio_pdf = pdf_recente
        else:
            raise Exception("❌ Nenhum PDF encontrado após download.")
        
        # Fecha aba extra se necessário
        self.fechar_abas_extras()
        
        # Baixa XLS
        print("📊 Agora gerando relatório em planilha XLS...")
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="saida_4"]'))).click()
        time.sleep(1)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="runReport"]'))).click()
        self.wait.until(EC.invisibility_of_element_located((By.ID, "divLoading")))
        time.sleep(8)
        
        self.fechar_abas_extras()
        
        # Encontra arquivo XLS mais recente
        arquivo_xls = encontrar_arquivo_mais_recente("xls")
        if not arquivo_xls:
            raise Exception("❌ Nenhum arquivo .xls encontrado após download.")
        
        print(f"📄 Arquivo encontrado: {arquivo_xls}")
        return relatorio_pdf, arquivo_xls
    
    def extrair_dados_produtos(self, df_produtos):
        """Extrai EAN e descrição completa dos produtos"""
        print("🔎 Iniciando extração de EAN e Descrição Completa...")
        
        # Faz login novamente se necessário
        if not self.navegador:
            self.setup_navegador()
            self.login()
        
        # Navega para tela de cadastro de produtos
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuBar"]/li[1]/a/span[2]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul1"]/li[1]/a/span'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul77"]/li[1]/a/span'))).click()
        self.wait.until(EC.invisibility_of_element_located((By.ID, 'divLoading')))
        print("📂 Tela de cadastro de produtos aberta.\n")
        
        eans, descricoes = [], []
        
        for i, codigo in enumerate(df_produtos['Código']):
            try:
                codigo_str = str(int(codigo))
                print(f"🔍 Processando código {i+1}/{len(df_produtos)}: {codigo_str}")
                
                # Insere código
                campo = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cod_redbarraEntrada"]')))
                campo.click()
                campo.send_keys(Keys.CONTROL, 'a')
                campo.send_keys(Keys.DELETE)
                time.sleep(0.3)
                campo.send_keys(codigo_str)
                campo.send_keys(Keys.ENTER)
                
                # Aguarda carregamento
                try:
                    WebDriverWait(self.navegador, 30).until(EC.invisibility_of_element_located((By.ID, 'divLoading')))
                except:
                    print(f"⚠️ Timeout no código {codigo_str}. Recarregando...")
                    self.recarregar_tela_cadastro()
                    continue
                
                # Coleta dados
                ean = self.navegador.find_element(By.XPATH, '//*[@id="cod_barra_principal"]').get_attribute("value")
                desc_completa = self.navegador.find_element(By.XPATH, '//*[@id="nom_prodcomp"]').get_attribute("value")
                
                eans.append(ean)
                descricoes.append(desc_completa)
                print(f"✅ Código {codigo} → EAN: {ean}, Desc: {desc_completa[:50]}...")
                
            except Exception as e:
                print(f"⚠️ Erro ao processar código {codigo}: {e}")
                eans.append("")
                descricoes.append("")
                continue
        
        return eans, descricoes
    
    def baixar_relatorio_estoque(self, codigos):
        """Baixa relatório de estoque por filial"""
        print("📦 Baixando relatório de SALDO EM ESTOQUE por filial...")
        
        # Navega para relatório de estoque
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuBar"]/li[11]/a/span[2]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul123"]/li[4]/a/span'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul127"]/li[1]/a/span'))).click()
        
        # Configura agrupamento por filial
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="agrup_fil_2"]'))).click()
        
        # Acessa aba de filtros
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabTabdhtmlgoodies_tabView1_1"]/a'))).click()
        
        # Insere códigos dos produtos
        campo_codigo = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cod_reduzidoEntrada"]')))
        for codigo in codigos:
            campo_codigo.send_keys(str(int(codigo)))
            campo_codigo.send_keys(Keys.ENTER)
            self.wait.until(EC.invisibility_of_element_located((By.ID, "divLoading")))
            time.sleep(0.2)
        
        # Configura para baixar XLS
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabTabdhtmlgoodies_tabView1_3"]/a'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="saida_4"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="runReport"]'))).click()
        self.wait.until(EC.invisibility_of_element_located((By.ID, "divLoading")))
        time.sleep(6)
        
        # Encontra arquivo baixado
        estoque_xls = encontrar_arquivo_mais_recente("xls")
        print(f"📄 XLS de estoque encontrado: {estoque_xls}")
        return estoque_xls
    
    def recarregar_tela_cadastro(self):
        """Recarrega a tela de cadastro de produtos"""
        self.navegador.refresh()
        time.sleep(5)
        
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuBar"]/li[1]/a/span[2]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul1"]/li[1]/a/span'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ul77"]/li[1]/a/span'))).click()
        self.wait.until(EC.invisibility_of_element_located((By.ID, 'divLoading')))
        print("🔁 Tela recarregada. Retomando processo...")
    
    def fechar_abas_extras(self):
        """Fecha abas extras abertas pelo sistema"""
        janelas = self.navegador.window_handles
        if len(janelas) > 1:
            self.navegador.switch_to.window(janelas[-1])
            self.navegador.close()
            self.navegador.switch_to.window(janelas[0])
            print("🪟 Aba extra fechada.")
    
    def fechar(self):
        """Fecha o navegador"""
        if self.navegador:
            self.navegador.quit()
            print("🧹 Navegador encerrado.\n")
