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
import tempfile

from config import *

def enviar_email_com_pdfs(relatorio_pdf, arquivos_etiquetas):
    """
    Envia emails com PDFs para cada filial
    
    Args:
        relatorio_pdf: Caminho do relatório principal
        arquivos_etiquetas: Dict {filial: caminho_pdf}
    """
    print("\n📨 Preparando envio de emails...")
    print(f"📧 Sender: {GMAIL_SENDER}")
    print(f"📋 Filiais no mapa: {list(EMAILS_FILIAIS.keys())}")
    print(f"🏷️ Etiquetas geradas: {list(arquivos_etiquetas.keys())}")
    
    if not SERVICE_ACCOUNT_PATH:
        print("❌ Service account credentials not found in environment!")
        return
    
    # Create temporary service account file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        try:
            # Parse the JSON to validate it
            creds_json = json.loads(SERVICE_ACCOUNT_PATH)
            json.dump(creds_json, temp_file)
            temp_file_path = temp_file.name
            print(f"✅ Temporary service account file created: {temp_file_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in service account credentials: {e}")
            return
        except Exception as e:
            print(f"❌ Error creating service account file: {e}")
            return
    
    try:
        # Configura credenciais
        scope = ["https://www.googleapis.com/auth/gmail.send"]
        
        creds = service_account.Credentials.from_service_account_file(
            temp_file_path,
            scopes=scope
        )
        
        delegated_creds = creds.with_subject(GMAIL_SENDER)
        service = build("gmail", "v1", credentials=delegated_creds)
        print("✅ Gmail API service initialized successfully")
        
        data = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        
        for filial, email in EMAILS_FILIAIS.items():
            # Verifica se há etiquetas para esta filial
            if filial not in arquivos_etiquetas:
                print(f"   ⚠️ Filial {filial} não tem etiquetas, pulando...")
                continue
            
            print(f"  📧 Preparando email para Filial {filial} -> {email}")
            
            try:
                # Cria mensagem
                msg = EmailMessage()
                msg["To"] = email
                msg["From"] = GMAIL_SENDER
                msg["Subject"] = f"ALTERAÇÕES DE PREÇOS - {data}"
                msg.set_content(f"""
Bom dia,

Segue em anexo o relatório de alterações de preços e as etiquetas correspondentes para a filial {filial}.

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
                result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
                
                print(f"    ✅ Email enviado para Filial {filial} (Message ID: {result.get('id', 'N/A')})")
                
            except Exception as e:
                print(f"    ❌ Erro ao enviar email para Filial {filial}: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Erro crítico no envio de emails: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
            print(f"🧹 Temporary file cleaned up: {temp_file_path}")
        except:
            pass
    
    print("\n✅ Todos os emails foram processados.")
