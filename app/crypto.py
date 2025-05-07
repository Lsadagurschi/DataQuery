# crypto.py
from cryptography.fernet import Fernet
import os
import base64
import hashlib

# Em produção, use variáveis de ambiente ou serviço de gerenciamento de segredos
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "your-secret-key-that-is-32-bytes")

def get_key():
    """Obtém a chave de criptografia"""
    if len(ENCRYPTION_KEY) < 32:
        # Se a chave for muito curta, derive uma chave de 32 bytes
        return base64.urlsafe_b64encode(hashlib.sha256(ENCRYPTION_KEY.encode()).digest())
    
    return base64.urlsafe_b64encode(ENCRYPTION_KEY[:32].encode())

def encrypt_data(data):
    """Criptografa dados sensíveis"""
    fernet = Fernet(get_key())
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """Descriptografa dados sensíveis"""
    fernet = Fernet(get_key())
    return fernet.decrypt(encrypted_data.encode()).decode()
