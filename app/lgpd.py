import streamlit as st
import json
import os
from datetime import datetime

# Arquivo para armazenar registros de consentimento
CONSENT_LOG_FILE = "consent_log.json"

def display_consent_form():
    """Exibe o formulário de consentimento para o usuário"""
    
    st.markdown("## Consentimento para Processamento de Dados")
    
    st.markdown("""
    Para fornecer e melhorar nossos serviços, a NeoQuery AI precisa processar alguns dos seus dados pessoais.
    Por favor, revise as seguintes opções e indique seu consentimento:
    """)
    
    consent_items = {
        "essential": {
            "title": "Processamento Essencial de Dados",
            "description": "Dados necessários para o funcionamento do serviço, como informações de conta e histórico de consultas.",
            "required": True,
            "default": True
        },
        "improvement": {
            "title": "Melhorias do Sistema",
            "description": "Usar suas consultas e feedback para melhorar a precisão do sistema de NLP.",
            "required": False,
            "default": True
        },
        "marketing": {
            "title": "Comunicações de Marketing",
            "description": "Receber e-mails sobre novos recursos, atualizações e ofertas.",
            "required": False,
            "default": False
        }
    }
    
    user_consent = {}
    
    for key, item in consent_items.items():
        if item["required"]:
            st.markdown(f"**{item['title']}** (Obrigatório)")
            st.markdown(item["description"])
            user_consent[key] = True
            st.checkbox("Entendi e concordo", value=True, disabled=True)
        else:
            st.markdown(f"**{item['title']}**")
            st.markdown(item["description"])
            user_consent[key] = st.checkbox("Concordo", value=item["default"], key=f"consent_{key}")
    
    st.markdown("""
    Você pode alterar suas preferências de consentimento a qualquer momento nas configurações da sua conta.
    Para mais informações, consulte nossa [Política de Privacidade](https://www.neoquery.ai/privacidade).
    """)
    
    agree = st.checkbox("Li e concordo com a Política de Privacidade e Termos de Serviço")
    
    if st.button("Confirmar", disabled=not agree):
        log_consent(user_consent)
        st.session_state.consent_given = True
        return user_consent
    
    return None

def log_consent(consent_data):
    """Registra o consentimento do usuário"""
    
    consents = []
    if os.path.exists(CONSENT_LOG_FILE):
        try:
            with open(CONSENT_LOG_FILE, 'r') as f:
                consents = json.load(f)
        except:
            consents = []
    
    # Adicionar novo registro de consentimento
    consent_record = {
        "user_email": st.session_state.get("user_email", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "ip_address": "127.0.0.1",  # Em produção, usar o IP real
        "consent_data": consent_data
    }
    
    consents.append(consent_record)
    
    with open(CONSENT_LOG_FILE, 'w') as f:
        json.dump(consents, f, indent=2)

def get_user_consent(user_email):
    """Obtém as preferências de consentimento do usuário"""
    
    if not os.path.exists(CONSENT_LOG_FILE):
        return None
    
    try:
        with open(CONSENT_LOG_FILE, 'r') as f:
            consents = json.load(f)
    except:
        return None
    
    # Obter o consentimento mais recente do usuário
    user_consents = [c for c in consents if c["user_email"] == user_email]
    
    if not user_consents:
        return None
    
    # Ordenar por timestamp (mais recente primeiro)
    user_consents.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return user_consents[0]["consent_data"]

def update_user_consent(user_email, consent_data):
    """Atualiza as preferências de consentimento do usuário"""
    
    log_consent(consent_data)
    return True

def data_export_request(user_email):
    """Processa uma solicitação de exportação de dados"""
    
    # Em uma implementação real, isso geraria um arquivo com todos os dados do usuário
    # Para esta demonstração, retornamos apenas um placeholder
    
    export_data = {
        "user_info": {
            "email": user_email,
            "export_date": datetime.now().isoformat()
        },
        "account_data": {},
        "query_history": [],
        "saved_queries": [],
        "consents": get_user_consent(user_email)
    }
    
    return export_data

def data_deletion_request(user_email):
    """Processa uma solicitação de exclusão de dados"""
    
    # Em uma implementação real, isso excluiria todos os dados do usuário
    # Para esta demonstração, apenas simulamos o processo
    
    deletion_record = {
        "user_email": user_email,
        "request_date": datetime.now().isoformat(),
        "completion_date": datetime.now().isoformat(),
        "status": "completed"
    }
    
    return deletion_record
