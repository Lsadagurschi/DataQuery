import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import yaml
from PIL import Image
import base64

# Importação dos módulos do sistema
from auth import authenticate_user, create_user, is_authenticated
from database import connect_database, execute_query, test_connection
# Em uma implementação real, você usaria um banco de dados adequado
# Este é apenas um exemplo para fins de demonstração

USER_DB_FILE = "users.json"

def _get_users():
    """Carrega os usuários de um arquivo JSON"""
    if not os.path.exists(USER_DB_FILE):
        return {}
    
    try:
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def _save_users(users):
    """Salva os usuários em um arquivo JSON"""
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def _hash_password(password):
    """Cria um hash da senha usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name, email, password, company):
    """Cria um novo usuário"""
    users = _get_users()
    
    if email in users:
        return False
    
    users[email] = {
        "name": name,
        "password": _hash_password(password),
        "company": company,
        "created_at": datetime.now().isoformat(),
        "plan": "trial",
        "plan_expires": (datetime.now() + timedelta(days=14)).isoformat()
    }
    
    _save_users(users)
    return True

def authenticate_user(email, password):
    """Autentica um usuário"""
    users = _get_users()
    
    if email not in users:
        return False
    
    if users[email]["password"] != _hash_password(password):
        return False
    
    return True

def is_authenticated():
    """Verifica se o usuário está autenticado na sessão atual"""
    return st.session_state.get("authenticated", False)

def get_user_details(email):
    """Obtém detalhes do usuário"""
    users = _get_users()
    
    if email not in users:
        return None
    
    user_data = users[email].copy()
    # Não retornar a senha hash
    user_data.pop("password", None)
    
    return user_data
  def update_user(email, details):
    """Atualiza detalhes do usuário"""
    users = _get_users()
    
    if email not in users:
        return False
    
    # Atualiza apenas os campos permitidos
    allowed_fields = ["name", "company", "plan", "plan_expires"]
    
    for field in allowed_fields:
        if field in details:
            users[email][field] = details[field]
    
    # Se a senha estiver sendo atualizada
    if "password" in details:
        users[email]["password"] = _hash_password(details["password"])
    
    _save_users(users)
    return True

def change_password(email, current_password, new_password):
    """Altera a senha do usuário"""
    if not authenticate_user(email, current_password):
        return False
    
    users = _get_users()
    users[email]["password"] = _hash_password(new_password)
    _save_users(users)
    
    return True

def delete_user(email, password):
    """Exclui um usuário"""
    if not authenticate_user(email, password):
        return False
    
    users = _get_users()
    
    if email in users:
        del users[email]
        _save_users(users)
        return True
    
    return False
