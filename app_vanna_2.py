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

# Configuração da página Streamlit
st.set_page_config(
    page_title="DataTalk - Consultas em Linguagem Natural para Operadora de Saúde",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    def connect(self, host, database, user, password, port):
        try:
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
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model_name = None
        self.vn = None
        self.initialized = False
        
    def initialize(self, api_key, model_name):
        """Inicializa a conexão com a API do Vanna"""
        self.api_key = api_key
        self.model_name = model_name
        
        try:
            self.vn = VannaDefault(model=model_name, api_key=api_key)
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
            # Gerar DDL para cada tabela
            tables = schema_df['table_name'].unique()
            for table in tables:
                table_cols = schema_df[schema_df['table_name'] == table]
                
                ddl = f"CREATE TABLE {table} (\n"
                for i, (_, row) in enumerate(table_cols.iterrows()):
                    col_def = f"    {row['column_name']} {row['data_type']}"
                    
                    # Adicionar constraints
                    if row['is_nullable'] == 'NO':
                        col_def += " NOT NULL"
                    
                    if row['column_default'] is not None:
                        col_def += f" DEFAULT {row['column_default']}"
                    
                    if i < len(table_cols) - 1:
                        col_def += ","
                        
                    ddl += col_def + "\n"
                
                ddl += ");"
                
                # Treinar Vanna com o DDL
                self.vn.train(ddl=ddl)
            
            # Adicionar documentação sobre o contexto
            self.vn.train(documentation="""
            Este banco de dados contém informações de uma operadora de saúde.
            As consultas devem ser focadas em dados relacionados a saúde, pacientes, 
            procedimentos médicos, planos de saúde e demais tópicos relacionados.
            """)
            
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
            return self.vn.generate_sql(question)
        except Exception as e:
            st.error(f"Erro ao gerar SQL: {e}")
            return None

    def execute_and_visualize(self, question):
        """Executa a consulta e gera visualização se possível"""
        if not self.initialized:
            return None, None
            
        try:
            # Gerar SQL
            sql = self.vn.generate_sql(question)
            
            if sql:
                # Executar SQL
                df = self.vn.run_sql(sql)
                
                # Tentar gerar visualização
                fig = self.vn.get_plotly_figure(question=question, sql=sql, df=df)
                
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
                    st.experimental_rerun()
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
            st.experimental_rerun()
        
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
                        
                        # Configurar Vanna.AI após conectar ao banco
                        with st.spinner("Configurando Vanna.AI..."):
                            api_key = st.text_input("API Key do Vanna.AI")
                            model_name = st.text_input("Nome do Modelo Vanna.AI", value="seu-modelo")
                            
                            if api_key and model_name:
                                if st.session_state.vanna_manager.initialize(api_key, model_name):
                                    st.success("Vanna.AI inicializado com sucesso!")
                                    
                                    # Treinar o modelo com o esquema do banco
                                    schema_df = st.session_state.db_manager.tables
                                    if schema_df is not None and not schema_df.empty:
                                        with st.spinner("Treinando modelo com esquema do banco..."):
                                            if st.session_state.vanna_manager.train_with_schema(schema_df):
                                                st.success("Modelo treinado com sucesso!")
                                            else:
                                                st.error("Erro ao treinar modelo!")
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
                            
                            if sql and df is not None:
                                st.code(sql, language="sql")
                                
                                # Adicionar à histórico
                                st.session_state.user_manager.add_to_history(
                                    st.session_state.username, query, sql
                                )
                                
                                # Mostrar resultados
                                st.dataframe(df)
                                
                                # Mostrar visualização se disponível
                                if fig is not None:
                                    st.plotly_chart(fig)
                                
                                # Opção para favoritar
                                fav_name = st.text_input("Nome para favoritar esta consulta (opcional):")
                                if fav_name and st.button("Favoritar"):
                                    st.session_state.user_manager.add_favorite(
                                        st.session_state.username, fav_name, query, sql
                                    )
                                    st.success(f"Consulta '{fav_name}' adicionada aos favoritos!")
                                
                                # Opção de feedback para melhorar o modelo
                                st.subheader("Feedback")
                                if st.button("Esta consulta está correta"):
                                    st.session_state.vanna_manager.train_with_query(query, sql)
                                    st.success("Obrigado pelo feedback! O modelo foi atualizado.")
                                
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
                        with st.expander(f"{item['timestamp']} - {item['query'][:50]}..."):
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
                    st.dataframe(st.session_state.db_manager.tables)
                    
                    # Opção para baixar o esquema
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
