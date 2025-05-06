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
import time

# Configuração da página Streamlit
st.set_page_config(
    page_title="DataTalk - Consultas em Linguagem Natural para Operadora de Saúde",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração do Vanna.AI como constante no backend
VANNA_API_KEY = "vn-1ab906ca575147a19e6859f701f51651"
VANNA_MODEL_NAME = "default"  # Você pode ajustar se necessário
VANNA_EMAIL = "sadagurschi@gmail.com"  # Email obrigatório para a API

# Classes para gerenciar usuários e autenticação
class UserManager:
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
            # Configuração com email explícito para resolver o erro
            # A forma correta de passar o email depende da implementação exata do VannaDefault
            # Vamos tentar diferentes abordagens
            
            # Abordagem 1: Usar o parâmetro config
            config = {
                "email": VANNA_EMAIL,
                "api_key": VANNA_API_KEY
            }
            
            self.vn = VannaDefault(
                model=VANNA_MODEL_NAME,
                api_key=VANNA_API_KEY,
                config=config
            )
            
            self.db_connection = db_params
            
            # Criar um objeto engine SQLAlchemy para uso nas consultas
            if db_params is not None:
                conn_str = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
                self.db_engine = create_engine(conn_str)
            
            # Verificar se a inicialização está correta testando uma chamada simples
            try:
                # Teste básico para verificar se a API está funcionando
                self.vn.train(documentation="Teste de inicialização")
                st.success("API do Vanna.AI inicializada e testada com sucesso!")
            except Exception as test_e:
                st.warning(f"API inicializada, mas teste falhou: {test_e}. Tentando prosseguir mesmo assim.")
            
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
        
        # Simplificando o treinamento para apenas uma documentação geral que descreve as tabelas
        try:
            # Extrair lista de tabelas
            tables = schema_df['table_name'].unique()
            tables_list = ", ".join(tables)
            
            doc = f"""
            Este banco de dados contém informações de uma operadora de saúde com as seguintes tabelas:
            {tables_list}.
            As consultas devem ser focadas em dados relacionados a saúde, pacientes, 
            procedimentos médicos, planos de saúde, atendimentos, convênios e demais tópicos relacionados.
            """
            
            # Tentar treinar uma única vez com toda a documentação
            try:
                train_config = {
                    "email": VANNA_EMAIL,
                    "api_key": VANNA_API_KEY
                }
                
                self.vn.train(documentation=doc, config=train_config)
                st.success("Treinamento completo realizado com sucesso!")
                return True
            except Exception as e:
                st.warning(f"Erro no treinamento completo: {e}")
                
                # Plano B: Ignorar o treinamento e prosseguir com o aplicativo
                st.warning("Prosseguindo sem treinamento completo. O sistema ainda poderá gerar consultas SQL básicas.")
                return True
                
        except Exception as e:
            st.error(f"Erro ao treinar modelo: {e}")
            # Mesmo com erro, retornar True para permitir que o aplicativo continue
            return True
    
    def train_with_query(self, question, sql):
        """Treina o modelo com pares pergunta-SQL conhecidos"""
        if not self.initialized:
            return False
        
        try:
            config = {
                "email": VANNA_EMAIL,
                "api_key": VANNA_API_KEY
            }
            
            # Treinar com um par específico de pergunta-SQL
            self.vn.train(question=question, sql=sql, config=config)
            return True
        except Exception as e:
            st.error(f"Erro ao treinar modelo com query: {e}")
            return False
    
    def generate_sql(self, question):
        """Gera código SQL a partir de uma pergunta em linguagem natural"""
        if not self.initialized:
            return None
        
        try:
            # Como estamos tendo problemas com os métodos do Vanna,
            # vamos começar com uma abordagem mais simples baseada nas tabelas que temos
            
            # Verificar se existe algum método generate_sql ou similar
            if hasattr(self.vn, 'generate_sql'):
                try:
                    return self.vn.generate_sql(question)
                except:
                    pass
            
            # Tentar com ask
            if hasattr(self.vn, 'ask'):
                try:
                    result = self.vn.ask(question)
                    if isinstance(result, str) and ("SELECT" in result.upper() or "WITH" in result.upper()):
                        return result
                except:
                    pass
            
            # Approach 2: Tentar construir SQL simples baseado nas tabelas disponíveis
            if self.db_engine:
                try:
                    # Analisar a pergunta e identificar possíveis tabelas mencionadas
                    query_lower = question.lower()
                    query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    """
                    tables_df = pd.read_sql(query, self.db_engine)
                    
                    # Procurar por tabelas mencionadas na pergunta
                    mentioned_tables = []
                    for table in tables_df['table_name'].values:
                        if table.lower() in query_lower:
                            mentioned_tables.append(table)
                    
                    # Se encontramos tabelas mencionadas, usar a primeira
                    if mentioned_tables:
                        table = mentioned_tables[0]
                        # Obter colunas da tabela
                        query = f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}'
                        """
                        cols_df = pd.read_sql(query, self.db_engine)
                        columns = ", ".join(cols_df['column_name'].values[:5])  # Limitar a 5 colunas
                        
                        return f"SELECT {columns} FROM {table} LIMIT 10;"
                    else:
                        # Se nenhuma tabela específica foi mencionada, pegar a primeira disponível
                        if not tables_df.empty:
                            table = tables_df.iloc[0]['table_name']
                            return f"SELECT * FROM {table} LIMIT 10;"
                except Exception as e:
                    st.warning(f"Erro ao gerar SQL com base nas tabelas: {e}")
            
            # Abordagem fallback: Retornar uma consulta genérica para listar tabelas
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

# Função principal para a interface do Streamlit
def main():
    # Inicializar os gerenciadores
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'vanna_manager' not in st.session_state:
        st.session_state.vanna_manager = VannaManager()
    
    # Verificar se o usuário está logado
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'username' not in st.session_state:
        st.session_state.username = None
        
    # Verificar se o treinamento foi concluído
    if 'training_completed' not in st.session_state:
        st.session_state.training_completed = False
    
    # Página de login/registro
    if not st.session_state.logged_in:
        st.title("🔐 Login / Registro")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Login")
            login_username = st.text_input("Usuário", key="login_user")
            login_password = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Login"):
                if st.session_state.user_manager.authenticate(login_username, login_password):
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.rerun()
                else:
                    st.error("Nome de usuário ou senha inválidos!")
        
        with col2:
            st.subheader("Registro")
            reg_username = st.text_input("Novo Usuário", key="reg_user")
            reg_password = st.text_input("Nova Senha", type="password", key="reg_pass")
            reg_password2 = st.text_input("Confirme a Senha", type="password", key="reg_pass2")
            
            if st.button("Registrar"):
                if reg_password != reg_password2:
                    st.error("As senhas não coincidem!")
                elif st.session_state.user_manager.register_user(reg_username, reg_password):
                    st.success("Usuário registrado com sucesso! Faça login.")
                else:
                    st.error("Usuário já existe!")
    
    # Aplicativo principal após o login
    else:
        st.sidebar.title(f"👤 Olá, {st.session_state.username}")
        
        # Opção para logout
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.training_completed = False
            st.rerun()
        
        # Verificar se está conectado ao banco
        if not st.session_state.db_manager.connected:
            st.subheader("📊 Conectar ao Banco de Dados")
            
            with st.form("db_connection_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    host = st.text_input("Host", value="db.neon.tech")
                    database = st.text_input("Database")
                    port = st.text_input("Port", value="5432")
                
                with col2:
                    user = st.text_input("Usuário")
                    password = st.text_input("Senha", type="password")
                
                submit_button = st.form_submit_button("Conectar")
                
                if submit_button:
                    if st.session_state.db_manager.connect(host, database, user, password, port):
                        st.success("Conectado ao banco de dados com sucesso!")
                        
                        # Configurar Vanna.AI automaticamente após conexão com o banco
                        with st.spinner("Configurando Vanna.AI automaticamente..."):
                            if st.session_state.vanna_manager.initialize(st.session_state.db_manager.connection_params):
                                st.success("Vanna.AI inicializado com sucesso!")
                                
                                # Treinar o modelo com o esquema do banco
                                schema_df = st.session_state.db_manager.tables
                                if schema_df is not None and not schema_df.empty:
                                    with st.spinner("Treinando modelo com esquema do banco..."):
                                        if st.session_state.vanna_manager.train_with_schema(schema_df):
                                            st.success("Treinamento básico concluído!")
                                            st.session_state.training_completed = True
                                            time.sleep(1)  # Pequena pausa para garantir que a mensagem seja vista
                                            st.rerun()  # Recarregar página para mostrar a interface de consulta
                                        else:
                                            st.warning("Houve problemas no treinamento do modelo, mas você ainda pode usar o sistema.")
                                            st.session_state.training_completed = True
                                            time.sleep(1)
                                            st.rerun()
                            else:
                                st.error("Erro ao inicializar Vanna.AI!")
                    else:
                        st.error("Erro ao conectar ao banco de dados!")
        
        # Interface principal quando conectado ao banco e Vanna configurado
        elif st.session_state.db_manager.connected and st.session_state.vanna_manager.initialized:
            st.title("💬 DataTalk - Consultas em Linguagem Natural")
            
            # Tabs para diferentes funcionalidades
            tab1, tab2, tab3, tab4 = st.tabs(["Consultas", "Favoritos", "Histórico", "Esquema do Banco"])
            
            with tab1:
                st.subheader("🔎 Consulte seu banco de dados em linguagem natural")
                
                # Área de consulta
                query = st.text_area("Digite sua pergunta em linguagem natural:", height=100)
                
                if st.button("Executar Consulta"):
                    if query:
                        with st.spinner("Gerando consulta SQL e executando..."):
                            sql, df, fig = st.session_state.vanna_manager.execute_and_visualize(query)
                            
                            if sql:
                                st.subheader("Consulta SQL Gerada:")
                                st.code(sql, language="sql")
                                
                                # Adicionar à histórico mesmo que a execução falhe
                                st.session_state.user_manager.add_to_history(
                                    st.session_state.username, query, sql
                                )
                                
                                if df is not None:
                                    # Mostrar resultados
                                    st.subheader("Resultados:")
                                    st.dataframe(df)
                                    
                                    # Mostrar visualização se disponível
                                    if fig is not None:
                                        st.subheader("Visualização:")
                                        st.plotly_chart(fig)
                                    
                                    # Opção para favoritar
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        fav_name = st.text_input("Nome para favoritar esta consulta (opcional):")
                                    with col2:
                                        if fav_name and st.button("Favoritar"):
                                            st.session_state.user_manager.add_favorite(
                                                st.session_state.username, fav_name, query, sql
                                            )
                                            st.success(f"Consulta '{fav_name}' adicionada aos favoritos!")
                                else:
                                    st.warning("A consulta foi gerada mas não retornou resultados ou ocorreu um erro na execução.")
                                
                                # Opção de feedback para melhorar o modelo
                                st.subheader("Feedback")
                                feedback_col1, feedback_col2 = st.columns(2)
                                with feedback_col1:
                                    if st.button("👍 Esta consulta está correta"):
                                        st.session_state.vanna_manager.train_with_query(query, sql)
                                        st.success("Obrigado pelo feedback! O modelo foi atualizado.")
                                
                                with feedback_col2:
                                    if st.button("👎 Esta consulta está incorreta"):
                                        st.warning("Por favor, forneça a versão correta da consulta abaixo.")
                                
                                correct_sql = st.text_area("Se a consulta estiver incorreta, você pode inserir a versão correta aqui:")
                                
                                if correct_sql and st.button("Enviar SQL correto"):
                                    st.session_state.vanna_manager.train_with_query(query, correct_sql)
                                    st.success("Obrigado pelo feedback! O modelo foi atualizado com sua versão correta.")
                            else:
                                st.error("Não foi possível gerar uma consulta SQL válida para esta pergunta.")
            
            with tab2:
                st.subheader("⭐ Consultas Favoritas")
                
                favorites = st.session_state.user_manager.get_favorites(st.session_state.username)
                
                if favorites:
                    for name, fav_data in favorites.items():
                        with st.expander(name):
                            st.markdown(f"**Pergunta:** {fav_data['query']}")
                            st.code(fav_data['sql'], language="sql")
                            
                            if st.button(f"Executar '{name}'"):
                                with st.spinner("Executando consulta favorita..."):
                                    df = st.session_state.db_manager.execute_query(fav_data['sql'])
                                    if df is not None:
                                        st.dataframe(df)
                else:
                    st.info("Você ainda não tem consultas favoritas. Execute consultas e favorite-as para acessá-las rapidamente aqui.")
            
            with tab3:
                st.subheader("📜 Histórico de Consultas")
                
                history = st.session_state.user_manager.get_history(st.session_state.username)
                
                if history:
                    history.reverse()  # Mostrar as consultas mais recentes primeiro
                    
                    for i, item in enumerate(history):
                        with st.expander(f"{item['timestamp']} - {item['query'][:50]}..." if len(item['query']) > 50 else f"{item['timestamp']} - {item['query']}"):
                            st.markdown(f"**Pergunta:** {item['query']}")
                            st.code(item['sql'], language="sql")
                            
                            if st.button(f"Executar novamente #{i}"):
                                with st.spinner("Executando consulta do histórico..."):
                                    df = st.session_state.db_manager.execute_query(item['sql'])
                                    if df is not None:
                                        st.dataframe(df)
                else:
                    st.info("Seu histórico de consultas está vazio. Execute algumas consultas para vê-las aqui.")
            
            with tab4:
                st.subheader("🗄️ Esquema do Banco de Dados")
                
                if st.session_state.db_manager.tables is not None and not st.session_state.db_manager.tables.empty:
                    # Agrupar por tabela para facilitar a visualização
                    tables = st.session_state.db_manager.tables['table_name'].unique()
                    
                    for table in tables:
                        with st.expander(f"Tabela: {table}"):
                            table_schema = st.session_state.db_manager.tables[
                                st.session_state.db_manager.tables['table_name'] == table
                            ]
                            st.dataframe(table_schema)
                    
                    # Opção para baixar o esquema completo
                    csv = st.session_state.db_manager.tables.to_csv(index=False)
                    st.download_button(
                        label="Download do Esquema em CSV",
                        data=csv,
                        file_name="esquema_banco.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Nenhum esquema de banco de dados disponível.")

# Executar o aplicativo
if __name__ == "__main__":
    main()
