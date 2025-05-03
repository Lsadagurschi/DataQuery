import os
import streamlit as st

# Função para obter secrets do Streamlit
def get_secret(key, default=None):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.environ.get(key, default)

# Variáveis de configuração
CONFIG = {
    "VANNA_API_KEY": get_secret("VANNA_API_KEY", "demo_key"),
    "VANNA_DEFAULT_MODEL": "default",
    "CACHE_ENABLED": True,
    "CACHE_TTL": 3600,
    "MAX_QUERY_TIME": 30,
    "MAX_ROWS_RETURN": 10000,
    "DEFAULT_CHART_TYPE": "bar",
    "MAX_ITEMS_IN_CHART": 20,
    "ALLOWED_OPERATIONS": ["SELECT"],
    "BLOCKED_TABLES": ["user_credentials", "admin_access"],
    "APP_NAME": "DataTalk",
    "APP_VERSION": "1.0.0",
    "COMPANY_NAME": "Sua Empresa",
}

# Função para obter uma configuração
def get_config(key, default=None):
    return CONFIG.get(key, default)

# Função para configurar uma nova chave
def set_config(key, value):
    CONFIG[key] = value
    return True
