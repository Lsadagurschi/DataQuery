import os
import streamlit as st
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
try:
    load_dotenv()
except:
    pass  # No .env file

# Função para obter secrets do Streamlit
def get_secret(key, default=None):
    """Obtém um segredo do Streamlit Cloud ou variável de ambiente"""
    try:
        if "secrets" in dir(st) and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)

# Configurações de segurança
SECURITY_CONFIG = {
    # Chaves de criptografia
    "JWT_SECRET_KEY": get_secret("JWT_SECRET_KEY", "seu_jwt_secret_super_secreto_123"),
    "ENCRYPTION_KEY": get_secret("ENCRYPTION_KEY", "sua_chave_de_criptografia_super_segura_456"),
    
    # Configurações de autenticação
    "AUTH_REQUIRED": True,
    "SESSION_TIMEOUT": 3600,  # segundos
    "FAILED_LOGIN_ATTEMPTS": 5,
    "ACCOUNT_LOCKOUT_TIME": 900,  # segundos
    
    # Proteção de dados
    "ANONYMIZE_SENSITIVE_DATA": True,
    "SENSITIVE_DATA_PATTERNS": {
        "CPF": r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
        "EMAIL": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        "PHONE": r'(\(?\d{2}\)?\s?)(\d{4,5}\-?\d{4})'
    },
    
    # Registro de atividades
    "ENABLE_AUDIT_LOGS": True,
    "LOG_LEVEL": "INFO",
    "LOG_RETENTION_DAYS": 90,
    
    # Conformidade LGPD
    "DATA_RETENTION_PERIOD": 180,  # dias
    "AUTO_DELETE_INACTIVE_USERS": True,
    "INACTIVE_USER_PERIOD": 365,  # dias
    
    # Controles de acesso
    "MAX_QUERY_SIZE": 10000,
    "ALLOWED_IP_RANGES": [],
    "BLOCKED_IP_RANGES": [],
}

def get_security_config(key, default=None):
    return SECURITY_CONFIG.get(key, default)
