# email_sender.py
import base64
from email.message import EmailMessage
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from config import EMAILS_FILIAIS
import os
import json

from config import *

def enviar_email_com_pdfs(relatorio_pdf, arquivos_etiquetas):
    """
    Envia emails com PDFs para cada filial
    
    Args:
        relatorio_pdf: Caminho do relatório principal
        arquivos_etiquetas: Dict {filial: caminho_pdf}
    """
    print("\n📨 Preparando envio de emails...")
    
    # Configura credenciais
    creds_env = SERVICE_ACCOUNT_PATH
    scope = ["https://www.googleapis.com/auth/gmail.send"]

    creds = Credentials.from_service_account_info(json.loads(creds_env), scopes=scope)
    delegated_creds = creds.with_subject(GMAIL_SENDER)
    service = build("gmail", "v1", credentials=delegated_creds)
    
    data = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    
    for filial, email in EMAILS_FILIAIS.items():
        # Verifica se há etiquetas para esta filial
        if filial not in arquivos_etiquetas:
            continue
        
        print(f"  📧 Preparando email para Filial {filial} -> {email}")
        
        try:
            # Cria mensagem
            msg = EmailMessage()
            msg["To"] = email
            msg["From"] = GMAIL_SENDER
            msg["Subject"] = f"ALTERAÇÕES DE PREÇOS - {data}"
            msg.set_content("""
Bom dia,

Segue em anexo o relatório de alterações de preços e as etiquetas correspondentes para sua filial.

Atenciosamente,
Sistema de Automação - Drogaria Cidade
""")
            
            # Anexa relatório global
            with open(relatorio_pdf, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="pdf",
                    filename=os.path.basename(relatorio_pdf)
                )
            
            # Anexa etiquetas da filial
            with open(arquivos_etiquetas[filial], "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="pdf",
                    filename=os.path.basename(arquivos_etiquetas[filial])
                )
            
            # Envia email
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
            
            print(f"    ✅ Email enviado para Filial {filial}")
            
        except Exception as e:
            print(f"    ❌ Erro ao enviar email para Filial {filial}: {e}")
    
    print("\n✅ Todos os emails foram processados.")
