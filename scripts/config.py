# config.py
import os
import base64
import json
from pathlib import Path

# === CONFIGURAÇÕES GERAIS ===
BASE_DIR = os.getcwd()  
ARQUIVOS_DIR = os.path.join(BASE_DIR, 'arquivos')
os.makedirs(ARQUIVOS_DIR, exist_ok=True)
DOWNLOAD_DIR = ARQUIVOS_DIR
SAIDA_DIR = ARQUIVOS_DIR

# === CONFIGURAÇÕES DO SISTEMA ===
LOGIN_URL = "http://drogcidade.ddns.net:4647/sgfpod1/Login.pod"
LOGIN_USUARIO = os.getenv("username")
LOGIN_SENHA = os.getenv("password")

# === CONFIGURAÇÕES DE EMAIL ===
SERVICE_ACCOUNT_PATH = os.getenv("GSA_CREDENTIALS")
GMAIL_SENDER = os.getenv("sender")

# Mapeamento de filiais para emails

def load_email_map():
    encoded_map = os.getenv("EMAIL_MAP_BASE64")
    """
    Loads base64 encoded JSON map from environment variable.
    Returns dictionary mapping filial → email.
    """
    if not encoded_map:
        raise ValueError("ERROR: EMAIL_MAP_B64 secret not found in environment!")

    try:
        decoded = base64.b64decode(encoded_map).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        raise ValueError(f"Invalid EMAIL_MAP_B64 format: {e}")

EMAILS_FILIAIS = load_email_map()

# === CONFIGURAÇÕES DO NAVEGADOR ===
CHROME_OPTIONS = {
    "headless": True,  # Mude para True se quiser headless
    "window_size": "1920,1080",
    "download_dir": DOWNLOAD_DIR
}

# === CONFIGURAÇÕES DAS ETIQUETAS ===
ETIQUETA_LARGURA_CM = 9
ETIQUETA_ALTURA_CM = 3
