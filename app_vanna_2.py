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
                                            st.success("Modelo treinado com sucesso!")
                                        else:
                                            st.warning("Houve alguns problemas no treinamento do modelo, mas você ainda pode usar o sistema.")
                            else:
                                st.error("Erro ao inicializar Vanna.AI!")
                    else:
                        st.error("Erro ao conectar ao banco de dados!")
        
        # Interface principal quando conectado ao banco e Vanna configurado
        elif st.session_state.vanna_manager.initialized:
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
