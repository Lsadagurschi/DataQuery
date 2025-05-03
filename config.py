import os
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

# Variáveis de configuração
CONFIG = {
    # Chave da API Vanna - usada para o serviço text-to-SQL
    "VANNA_API_KEY": get_secret("VANNA_API_KEY", "demo_key"),
    
    # Modelo padrão do Vanna
    "VANNA_DEFAULT_MODEL": "default",
    
    # Configurações do cache
    "CACHE_ENABLED": True,
    "CACHE_TTL": 3600,  # Tempo de vida do cache em segundos
    
    # Limitações de consulta
    "MAX_QUERY_TIME": 30,  # Tempo máximo de execução em segundos
    "MAX_ROWS_RETURN": 10000,  # Número máximo de linhas retornadas
    
    # Configurações de visualização
    "DEFAULT_CHART_TYPE": "bar",
    "MAX_ITEMS_IN_CHART": 20,
    
    # Configurações de segurança
    "ALLOWED_OPERATIONS": ["SELECT"],
    "BLOCKED_TABLES": ["user_credentials", "admin_access"],
    
    # Configurações da aplicação
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
