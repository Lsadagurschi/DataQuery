import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import uuid

# Constantes para armazenamento
QUERY_HISTORY_FILE = "query_history.json"
SAVED_QUERIES_FILE = "saved_queries.json"
GOLD_LIST_FILE = "gold_list.json"

def _get_query_history():
    """Carrega o histórico de consultas"""
    if not os.path.exists(QUERY_HISTORY_FILE):
        return []
    
    try:
        with open(QUERY_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def _save_query_history(history):
    """Salva o histórico de consultas"""
    with open(QUERY_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def _get_saved_queries():
    """Carrega as consultas salvas"""
    if not os.path.exists(SAVED_QUERIES_FILE):
        return []
    
    try:
        with open(SAVED_QUERIES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def _save_saved_queries(queries):
    """Salva as consultas salvas"""
    with open(SAVED_QUERIES_FILE, 'w') as f:
        json.dump(queries, f, indent=2)

def _get_gold_list():
    """Carrega a lista de consultas exemplares"""
    if not os.path.exists(GOLD_LIST_FILE):
        return []
    
    try:
        with open(GOLD_LIST_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def _save_gold_list(gold_list):
    """Salva a lista de consultas exemplares"""
    with open(GOLD_LIST_FILE, 'w') as f:
        json.dump(gold_list, f, indent=2)

def save_query(query_text, sql_text, user_email, category=None, name=None):
    """Salva uma consulta no histórico e opcionalmente como consulta salva"""
    
    # Adicionar ao histórico
    history = _get_query_history()
    
    history_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "user_email": user_email,
        "query_text": query_text,
        "sql_text": sql_text,
        "status": "success"  # Assumindo sucesso
    }
    
    history.append(history_entry)
    _save_query_history(history)
    
    # Se for para salvar como consulta favorita (com nome)
    if name:
        saved_queries = _get_saved_queries()
        
        saved_entry = {
            "id": str(uuid.uuid4()),
            "name": name,
            "category": category if category else "Geral",
            "created_at": datetime.now().isoformat(),
            "user_email": user_email,
            "query_text": query_text,
            "sql_text": sql_text,
            "starred": False
        }
        
        saved_queries.append(saved_entry)
        _save_saved_queries(saved_queries)
    
    return True

def get_history(user_email, limit=10):
    """Obtém o histórico de consultas de um usuário"""
    history = _get_query_history()
    
    # Filtrar por e-mail e ordenar por timestamp (mais recente primeiro)
    user_history = [
        (h["timestamp"], h["query_text"], h["sql_text"])
        for h in history
        if h["user_email"] == user_email
    ]
    
    user_history.sort(reverse=True)  # Ordenar por timestamp decrescente
    
    return user_history[:limit]  # Retornar apenas os mais recentes

def get_saved_queries(user_email, category=None):
    """Obtém as consultas salvas de um usuário"""
    saved_queries = _get_saved_queries()
    
    # Filtrar por e-mail e categoria
    if category:
        user_queries = [
            q for q in saved_queries
            if q["user_email"] == user_email and q["category"] == category
        ]
    else:
        user_queries = [
            q for q in saved_queries
            if q["user_email"] == user_email
        ]
    
    # Ordenar por data de criação (mais recente primeiro)
    user_queries.sort(key=lambda x: x["created_at"], reverse=True)
    
    return user_queries

def add_to_gold_list(query_text, sql_text, user_email):
    """Adiciona uma consulta à lista de exemplos de referência"""
    gold_list = _get_gold_list()
    
    # Verificar se consulta similar já existe
    for item in gold_list:
        if query_text.lower() == item["query"].lower():
            return False  # Já existe
    
    # Adicionar à gold list
    gold_list.append({
        "id": str(uuid.uuid4()),
        "query": query_text,
        "sql": sql_text,
        "added_at": datetime.now().isoformat(),
        "added_by": user_email
    })
    
    # Limitar a lista a 100 exemplos
    if len(gold_list) > 100:
        gold_list = gold_list[-100:]
    
    _save_gold_list(gold_list)
    return True

def get_gold_list():
    """Obtém a lista de consultas exemplares"""
    gold_list = _get_gold_list()
    
    # Ordenar por data de adição (mais recente primeiro)
    gold_list.sort(key=lambda x: x["added_at"], reverse=True)
    
    return gold_list
