import streamlit as st
import pandas as pd
import psycopg2
import pymysql
import pyodbc
import cx_Oracle
import sqlparse
import json
import os
from datetime import datetime

# Constante para armazenar configurações de conexão
CONN_CONFIG_FILE = "connections.json"

def _get_connections():
    """Carrega as conexões salvas de um arquivo JSON"""
    if not os.path.exists(CONN_CONFIG_FILE):
        return {}
    
    try:
        with open(CONN_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def _save_connections(connections):
    """Salva as conexões em um arquivo JSON"""
    with open(CONN_CONFIG_FILE, 'w') as f:
        json.dump(connections, f, indent=2)

def test_connection(db_type, host, port, database, username, password):
    """Testa a conexão com o banco de dados"""
    try:
        conn = create_connection(db_type, host, port, database, username, password)
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao conectar: {str(e)}")
        return False

def create_connection(db_type, host, port, database, username, password):
    """Cria uma conexão com o banco de dados"""
    if db_type == "PostgreSQL":
        return psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
    elif db_type == "MySQL":
        return pymysql.connect(
            host=host,
            port=int(port),
            database=database,
            user=username,
            password=password
        )
    elif db_type == "SQL Server":
        conn_str = f'DRIVER={{SQL Server}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password}'
        return pyodbc.connect(conn_str)
    elif db_type == "Oracle":
        dsn = cx_Oracle.makedsn(host, port, service_name=database)
        return cx_Oracle.connect(username, password, dsn)
    else:
        raise ValueError(f"Tipo de banco de dados não suportado: {db_type}")

def connect_database(db_info, name=None):
    """Conecta ao banco de dados e salva a configuração"""
    # Extrair informações
    db_type = db_info["type"]
    host = db_info["host"]
    port = db_info["port"]
    database = db_info["database"]
    username = db_info["username"]
    password = db_info["password"]
    
    # Testar conexão
    if test_connection(db_type, host, port, database, username, password):
        # Salvar configuração se tiver um nome
        if name:
            connections = _get_connections()
            
            connections[name] = {
                "type": db_type,
                "host": host,
                "port": port,
                "database": database,
                "username": username,
                "password": password,  # Em uma implementação real, isto seria criptografado
                "created_at": datetime.now().isoformat()
            }
            
            _save_connections(connections)
        
        return True
    else:
        return False

def execute_query(query, db_info):
    """Executa uma consulta SQL e retorna os resultados como DataFrame"""
    try:
        # Criar conexão
        conn = create_connection(
            db_info["type"],
            db_info["host"],
            db_info["port"],
            db_info["database"],
            db_info["username"],
            db_info["password"]
        )
        
        # Executar consulta
        df = pd.read_sql_query(query, conn)
        
        # Fechar conexão
        conn.close()
        
        # Registrar a consulta no histórico
        _log_query(query)
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao executar consulta: {str(e)}")
        return pd.DataFrame()

def get_schema_info(db_info):
    """Obtém informações sobre o schema do banco de dados"""
    try:
        # Criar conexão
        conn = create_connection(
            db_info["type"],
            db_info["host"],
            db_info["port"],
            db_info["database"],
            db_info["username"],
            db_info["password"]
        )
        
        cursor = conn.cursor()
        
        schema_info = {
            "tables": [],
            "relationships": []
        }
        
        # Obter lista de tabelas
        if db_info["type"] == "PostgreSQL":
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Para cada tabela, obter as colunas
            for table in tables:
                cursor.execute(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = '{table}'
                """)
                
                columns = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]
                
                schema_info["tables"].append({
                    "name": table,
                    "columns": columns
                })
                
            # Obter chaves estrangeiras para relações
            cursor.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu 
                      ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'FOREIGN KEY'
            """)
            
            for row in cursor.fetchall():
                schema_info["relationships"].append({
                    "table": row[0],
                    "column": row[1],
                    "foreign_table": row[2],
                    "foreign_column": row[3]
                })
        
        # Implementações similares para outros bancos de dados
        
        conn.close()
        return schema_info
    
    except Exception as e:
        st.error(f"Erro ao obter schema: {str(e)}")
        return None

def _log_query(query):
    """Registra a consulta no log de consultas"""
    # Em uma implementação real, isso seria feito em um banco de dados
    
    # Para esta demonstração, apenas registra em um arquivo
    with open("query_log.txt", "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"[{timestamp}] {query}\n")
