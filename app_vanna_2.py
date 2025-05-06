import streamlit as st
import pandas as pd
import json
import hashlib
import os
import psycopg2
from sqlalchemy import create_engine
import vanna
from vanna.remote import VannaDefault
import plotly.express as px
import re

# Configuração da página Streamlit
st.set_page_config(
    page_title="DataTalk - Consultas em Linguagem Natural para Operadora de Saúde",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração do Vanna.AI como constante no backend
VANNA_API_KEY = "vn-1ab906ca575147a19e6859f701f51651"
VANNA_MODEL_NAME = "default"  # Você pode ajustar se necessário

# Classes para gerenciar usuários e autenticação
class UserManager:
    # [código da classe permanece igual]
    def __init__(self, user_file='users.json'):
        self.user_file = user_file
        if not os.path.exists(user_file):
            with open(user_file, 'w') as f:
                json.dump({}, f)
        
        with open(user_file, 'r') as f:
            self.users = json.load(f)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password):
        if username in self.users:
            return False
        
        self.users[username] = {
            'password_hash': self.hash_password(password),
            'favorite_queries': {},
            'history': []
        }
        self._save_users()
        return True
    
    def authenticate(self, username, password):
        if username not in self.users:
            return False
        
        if self.users[username]['password_hash'] == self.hash_password(password):
            return True
        return False
    
    def add_to_history(self, username, query, sql):
        if username in self.users:
            self.users[username]['history'].append({
                'query': query,
                'sql': sql,
                'timestamp': pd.Timestamp.now().isoformat()
            })
            self._save_users()
    
    def add_favorite(self, username, query_name, query, sql):
        if username in self.users:
            self.users[username]['favorite_queries'][query_name] = {
                'query': query,
                'sql': sql
            }
            self._save_users()
    
    def get_favorites(self, username):
        if username in self.users:
            return self.users[username]['favorite_queries']
        return {}
    
    def get_history(self, username):
        if username in self.users:
            return self.users[username]['history']
        return []
    
    def _save_users(self):
        with open(self.user_file, 'w') as f:
            json.dump(self.users, f)

# Classe para gerenciar conexões de banco de dados
class DatabaseManager:
    # [código da classe permanece igual]
    def __init__(self):
        self.connection = None
        self.engine = None
        self.connected = False
        self.tables = []
        self.connection_params = {}
    
    def connect(self, host, database, user, password, port):
        try:
            # Armazenar os parâmetros de conexão para uso posterior
            self.connection_params = {
                'host': host,
                'dbname': database,
                'user': user,
                'password': password,
                'port': port
            }
            
            connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            self.engine = create_engine(connection_string)
            self.connection = self.engine.connect()
            self.connected = True
            
            # Carregar esquema do banco
            self.load_schema()
            return True
        except Exception as e:
            st.error(f"Erro ao conectar no banco de dados: {e}")
            self.connected = False
            return False
    
    def load_schema(self):
        """Carrega o esquema do banco de dados para ser usado no treinamento do Vanna"""
        if not self.connected:
            return
            
        # Consulta para obter informações sobre tabelas e colunas
        query = """
        SELECT 
            table_schema, 
            table_name, 
            column_name, 
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM 
            information_schema.columns
        WHERE 
            table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY 
            table_schema, table_name, ordinal_position;
        """
        
        try:
            df = pd.read_sql(query, self.connection)
            self.tables = df
            return df
        except Exception as e:
            st.error(f"Erro ao carregar esquema: {e}")
            return pd.DataFrame()
    
    def execute_query(self, query):
        if not self.connected:
            return None
        
        try:
            return pd.read_sql(query, self.connection)
        except Exception as e:
            st.error(f"Erro ao executar consulta: {e}")
            return None

# Classe para gerenciar a integração com o Vanna.AI
class VannaManager:
    def __init__(self):
        self.vn = None
        self.initialized = False
        self.db_connection = None
        self.db_engine = None
        
    def initialize(self, db_params=None):
        """Inicializa a conexão com a API do Vanna com valores hardcoded"""
        try:
            # Usar os valores constantes definidos no início do código
            self.vn = VannaDefault(model=VANNA_MODEL_NAME, api_key=VANNA_API_KEY)
            self.db_connection = db_params
            
            # Criar um objeto engine SQLAlchemy para uso nas consultas
            if db_params is not None:
                conn_str = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
                self.db_engine = create_engine(conn_str)
            
            self.initialized = True
            return True
        except Exception as e:
            st.error(f"Erro ao inicializar Vanna.AI: {e}")
            self.initialized = False
            return False
    
    def train_with_schema(self, schema_df):
        """Treina o modelo com informações de esquema do banco"""
        if not self.initialized or schema_df is None:
            return False
        
        try:
            # Treinar com documentação geral primeiro
            self.vn.train(documentation="""
            Este banco de dados contém informações de uma operadora de saúde.
            As consultas devem ser focadas em dados relacionados a saúde, pacientes, 
            procedimentos médicos, planos de saúde, atendimentos, convênios e demais tópicos relacionados.
            Não retorne dados relacionados a produtos eletrônicos ou outros setores.
            """)
            
            # Gerar DDL simplificado para cada tabela
            tables = schema_df['table_name'].unique()
            for table in tables:
                table_cols = schema_df[schema_df['table_name'] == table]
                
                # Criar documentação para esta tabela
                cols_text = ", ".join([f"{row['column_name']} ({row['data_type']})" 
                                     for _, row in table_cols.iterrows()])
                doc = f"A tabela {table} contém as seguintes colunas: {cols_text}"
                
                try:
                    self.vn.train(documentation=doc)
                except Exception as e:
                    st.warning(f"Aviso ao treinar documentação para tabela {table}: {e}")
                
                # Criar DDL simplificado 
                try:
                    ddl = f"CREATE TABLE {table} (\n"
                    for i, (_, row) in enumerate(table_cols.iterrows()):
                        col_def = f"    {row['column_name']} {row['data_type']}"
                        if i < len(table_cols) - 1:
                            col_def += ","
                        ddl += col_def + "\n"
                    ddl += ");"
                    
                    # Treinar com o DDL
                    self.vn.train(ddl=ddl)
                except Exception as e:
                    st.warning(f"Aviso ao treinar DDL para tabela {table}: {e}")
            
            return True
        except Exception as e:
            st.error(f"Erro ao treinar modelo: {e}")
            return False
    
    def train_with_query(self, question, sql):
        """Treina o modelo com pares pergunta-SQL conhecidos"""
        if not self.initialized:
            return False
        
        try:
            # Treinar com um par específico de pergunta-SQL
            self.vn.train(question=question, sql=sql)
            return True
        except Exception as e:
            st.error(f"Erro ao treinar modelo com query: {e}")
            return False
    
    def generate_sql(self, question):
        """Gera código SQL a partir de uma pergunta em linguagem natural"""
        if not self.initialized:
            return None
        
        try:
            # Primeiro, tente usar o método direct_sql se disponível
            try:
                if hasattr(self.vn, 'direct_sql'):
                    return self.vn.direct_sql(question)
            except:
                pass
            
            # Vamos tentar múltiplas abordagens para garantir que temos uma consulta SQL
            
            # Abordagem 1: Usar ask e verificar se é SQL
            try:
                response = self.vn.ask(question)
                if response and isinstance(response, str):
                    # Verificar se a resposta parece SQL (começa com SELECT, INSERT, UPDATE, DELETE, etc)
                    if re.search(r'^(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|ALTER)', response.strip(), re.IGNORECASE):
                        return response.strip()
            except:
                pass
                
            # Abordagem 2: Tentar construir SQL simples baseado nas tabelas disponíveis
            if self.db_engine:
                try:
                    # Pegar uma lista de tabelas
                    query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    LIMIT 1;
                    """
                    result = pd.read_sql(query, self.db_engine)
                    if not result.empty:
                        sample_table = result.iloc[0]['table_name']
                        return f"SELECT * FROM {sample_table} LIMIT 10;"
                except:
                    pass
            
            # Abordagem 3: Retornar uma consulta genérica para listar tabelas
            return """
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name;
            """
        except Exception as e:
            st.error(f"Erro ao gerar SQL: {e}")
            return None

    def execute_and_visualize(self, question):
        """Executa a consulta e gera visualização se possível"""
        if not self.initialized:
            return None, None, None
            
        try:
            # Gerar SQL usando nosso método personalizado
            sql = self.generate_sql(question)
            
            if sql:
                # Executar SQL diretamente usando SQLAlchemy
                try:
                    if self.db_engine:
                        df = pd.read_sql(sql, self.db_engine)
                    else:
                        # Caso não tenha engine, tente usar o método do Vanna
                        conn_str = f"postgresql://{self.db_connection['user']}:{self.db_connection['password']}@{self.db_connection['host']}:{self.db_connection['port']}/{self.db_connection['dbname']}"
                        df = self.vn.run_sql(sql, connection_string=conn_str)
                except Exception as exec_error:
                    st.error(f"Erro ao executar SQL: {exec_error}")
                    return sql, None, None
                
                # Gerar visualização simplificada
                fig = None
                try:
                    # Tentar criar um gráfico básico se tivermos pelo menos 2 colunas
                    if df is not None and not df.empty and len(df.columns) >= 2:
                        # Se tivermos poucos dados, usar gráfico de barras
                        if len(df) <= 15:
                            # Escolher as primeiras duas colunas
                            x_col = df.columns[0]
                            y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
                            fig = px.bar(df, x=x_col, y=y_col, title=question)
                        else:
                            # Para muitos dados, usar linha
                            x_col = df.columns[0]
                            y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
                            fig = px.line(df, x=x_col, y=y_col, title=question)
                except Exception as viz_error:
                    st.warning(f"Não foi possível gerar visualização: {viz_error}")
                    fig = None
                
                return sql, df, fig
            return None, None, None
        except Exception as e:
            st.error(f"Erro ao executar e visualizar: {e}")
            return None, None, None

# [O resto do código permanece igual]
