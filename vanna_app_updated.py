import streamlit as st
import pandas as pd
import time
import os
import plotly.express as px
from sqlalchemy import create_engine, text

# Importação atualizada do Vanna
try:
    import vanna
    VANNA_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False
    st.warning("Biblioteca Vanna não está disponível. Algumas funções serão limitadas.")

# Configuração da página
st.set_page_config(
    page_title="DataTalk - Consulta SQL por Linguagem Natural com Vanna.ai", 
    page_icon="💬", 
    layout="wide"
)

# Função para obter secrets do Streamlit
def get_secret(key, default=None):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.environ.get(key, default)

# Configurações da API Vanna
VANNA_API_KEY = get_secret("vn-1ab906ca575147a19e6859f701f51651", "")

# Inicializar estados da sessão
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False
if 'is_demo' not in st.session_state:
    st.session_state.is_demo = False
if 'vanna_client' not in st.session_state:
    st.session_state.vanna_client = None
if 'current_sql' not in st.session_state:
    st.session_state.current_sql = None
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'db_engine' not in st.session_state:
    st.session_state.db_engine = None

# Função para exibir o cabeçalho
def display_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("💬")  # Emoji como logo
    with col2:
        st.title("DataTalk + Vanna.ai")
        st.write("Consulte seu banco de dados usando linguagem natural avançada")
    st.divider()

# Função para página de login
def show_login_page():
    st.title("DataTalk - Login")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            # Login simplificado
            if username == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.session_state.user = {"username": username}
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

# Inicializar cliente Vanna (API atualizada)
def init_vanna_client(api_key):
    if not VANNA_AVAILABLE:
        return None
    
    try:
        # Inicialização atualizada para versões mais recentes do Vanna
        vanna_client = vanna.setup_vanna(api_key=api_key)
        return vanna_client
    except Exception as e:
        st.error(f"Erro ao inicializar cliente Vanna: {str(e)}")
        return None

# Função para conectar ao banco de dados
def connect_to_database(db_type, host, port, database, username, password):
    try:
        if db_type == "PostgreSQL":
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "MySQL":
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:
            st.error("Tipo de banco de dados não suportado!")
            return False
            
        engine = create_engine(connection_string)
        
        # Testar conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        st.session_state.db_engine = engine
        return True
    except Exception as e:
        st.error(f"Erro na conexão: {str(e)}")
        return False

# Função para gerar SQL com Vanna.ai (API atualizada)
def generate_vanna_sql(query, vanna_client):
    if not VANNA_AVAILABLE or vanna_client is None:
        # Fallback para demonstração
        return generate_demo_sql(query)
    
    try:
        # API atualizada para versões mais recentes do Vanna
        sql = vanna_client.generate_sql(question=query)
        return sql
    except Exception as e:
        st.error(f"Erro ao gerar SQL com Vanna: {str(e)}")
        return generate_demo_sql(query)

# Função para geração de SQL de demonstração
def generate_demo_sql(query):
    if "produtos" in query.lower() or "vendidos" in query.lower():
        return """
        SELECT p.product_name, SUM(oi.quantity) as total_vendas
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_name
        ORDER BY total_vendas DESC
        LIMIT 5;
        """
    elif "clientes" in query.lower():
        return """
        SELECT c.first_name, c.last_name, COUNT(o.order_id) as num_pedidos
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.first_name, c.last_name
        ORDER BY num_pedidos DESC
        LIMIT 10;
        """
    else:
        return """
        SELECT * FROM products LIMIT 5;
        """

# Função para executar SQL no banco de dados
def execute_database_query(sql, engine):
    try:
        df = pd.read_sql_query(sql, engine)
        return df
    except Exception as e:
        st.error(f"Erro ao executar SQL: {str(e)}")
        return None

# Função para executar consulta simulada (modo Demo)
def execute_demo_query(sql):
    if "products" in sql and "order_items" in sql:
        return pd.DataFrame({
            'product_name': ['Notebook Pro', 'Smartphone X', 'Monitor 4K', 'Teclado Wireless', 'Mouse Gamer'],
            'total_vendas': [324, 286, 195, 178, 156]
        })
    elif "customers" in sql:
        return pd.DataFrame({
            'first_name': ['Ana', 'Carlos', 'Maria', 'João', 'Luciana'],
            'last_name': ['Silva', 'Oliveira', 'Santos', 'Pereira', 'Costa'],
            'num_pedidos': [8, 6, 5, 4, 3]
        })
    else:
        return pd.DataFrame({
            'product_id': [1, 2, 3, 4, 5],
            'product_name': ['Notebook Pro', 'Smartphone X', 'Monitor 4K', 'Teclado Wireless', 'Mouse Gamer'],
            'price': [3999.99, 2499.99, 1299.99, 199.99, 149.99]
        })

# Função principal
def main():
    # Verificar autenticação
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Exibir cabeçalho
    display_header()
    
    # Barra lateral
    with st.sidebar:
        st.header("🔗 Configuração")
        
        # Configuração do Vanna.ai
        with st.expander("Configuração Vanna.ai", expanded=False):
            vanna_api_key = st.text_input(
                "API Key Vanna.ai",
                value=VANNA_API_KEY,
                type="password",
                help="Insira sua API key do Vanna.ai"
            )
            
            if st.button("Configurar Vanna.ai"):
                if vanna_api_key:
                    vanna_client = init_vanna_client(vanna_api_key)
                    if vanna_client:
                        st.session_state.vanna_client = vanna_client
                        st.success("Cliente Vanna.ai configurado com sucesso!")
                else:
                    st.warning("Por favor, forneça uma API key válida.")
        
        # Configuração do banco de dados
        with st.expander("Configuração do Banco de Dados", expanded=True):
            db_type = st.selectbox(
                "Tipo de Banco de Dados",
                ["PostgreSQL", "MySQL"],
                index=0
            )
            
            host = st.text_input("Host", value="localhost")
            port = st.text_input("Porta", value="5432" if db_type == "PostgreSQL" else "3306")
            database = st.text_input("Nome do Banco", value="neondb")
            username = st.text_input("Usuário", value="postgres")
            password = st.text_input("Senha", type="password")
            
            if st.button("Conectar ao Banco"):
                if connect_to_database(db_type, host, port, database, username, password):
                    st.session_state.is_connected = True
                    st.session_state.is_demo = False
                    st.success("Banco de dados conectado com sucesso!")
        
        # Botão para modo demo
        if st.button("Usar Modo Demo"):
            st.session_state.is_demo = True
            st.success("Modo de demonstração ativado!")
        
        # Status da conexão
        if st.session_state.is_connected:
            st.success(f"Conectado ao banco {database}")
        
        # Histórico de consultas
        if st.session_state.query_history:
            st.header("📜 Histórico")
            for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
                with st.expander(f"Consulta {i+1}"):
                    st.code(item, language="sql")
        
        # Botão de logout
        if st.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Área principal
    if st.session_state.is_connected or st.session_state.is_demo:
        st.header("💬 Faça sua pergunta")
        
        # Input para a pergunta em linguagem natural
        query = st.text_area(
            "O que você gostaria de saber?",
            placeholder="Ex: Quais são os 5 produtos mais vendidos?",
            height=100
        )
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Gerar SQL"):
                if query:
                    with st.spinner("Gerando SQL..."):
                        if st.session_state.vanna_client and not st.session_state.is_demo:
                            sql = generate_vanna_sql(query, st.session_state.vanna_client)
                        else:
                            # Usar geração simulada
                            sql = generate_demo_sql(query)
                        
                        st.session_state.current_sql = sql
                        st.session_state.query = query
                        st.success("SQL gerado com sucesso!")
        
        with col2:
            if st.button("Executar") and st.session_state.current_sql:
                with st.spinner("Executando consulta..."):
                    if st.session_state.is_demo:
                        results = execute_demo_query(st.session_state.current_sql)
                    else:
                        results = execute_database_query(st.session_state.current_sql, st.session_state.db_engine)
                    
                    st.session_state.current_results = results
                    if st.session_state.current_sql not in st.session_state.query_history:
                        st.session_state.query_history.append(st.session_state.current_sql)
                    st.success("Consulta executada com sucesso!")
        
        # Exibir resultados se disponíveis
        if st.session_state.current_sql:
            tabs = st.tabs(["📊 Resultados", "📝 SQL", "📈 Visualização"])
            
            with tabs[0]:
                if "current_results" in st.session_state and st.session_state.current_results is not None:
                    st.dataframe(st.session_state.current_results, use_container_width=True)
                else:
                    st.info("Execute a consulta para ver resultados")
            
            with tabs[1]:
                st.code(st.session_state.current_sql, language="sql")
            
            with tabs[2]:
                if "current_results" in st.session_state and st.session_state.current_results is not None:
                    df = st.session_state.current_results
                    if len(df.columns) >= 2:
                        x_col = df.columns[0]
                        
                        # Tente encontrar uma coluna numérica para o eixo Y
                        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                        if numeric_cols:
                            y_col = numeric_cols[0]
                        else:
                            y_col = df.columns[0]
                        
                        # Opções para o gráfico
                        st.subheader("Configurações de visualização")
                        chart_type = st.selectbox("Tipo de gráfico", ["Barra", "Linha", "Pizza", "Dispersão"])
                        col1, col2 = st.columns(2)
                        with col1:
                            x_axis = st.selectbox("Eixo X", df.columns.tolist(), index=df.columns.get_loc(x_col))
                        with col2:
                            y_options = numeric_cols if numeric_cols else df.columns.tolist()
                            y_default = numeric_cols.index(y_col) if y_col in numeric_cols and numeric_cols else 0
                            y_axis = st.selectbox("Eixo Y", y_options, index=min(y_default, len(y_options)-1) if y_options else 0)
                        
                        # Criar gráfico
                        try:
                            if chart_type == "Barra":
                                fig = px.bar(df, x=x_axis, y=y_axis, title=f"{y_axis} por {x_axis}")
                                st.plotly_chart(fig)
                            elif chart_type == "Linha":
                                fig = px.line(df, x=x_axis, y=y_axis, title=f"{y_axis} por {x_axis}")
                                st.plotly_chart(fig)
                            elif chart_type == "Pizza":
                                fig = px.pie(df, names=x_axis, values=y_axis, title=f"Distribuição de {y_axis}")
                                st.plotly_chart(fig)
                            else:  # Dispersão
                                fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
                                st.plotly_chart(fig)
                        except Exception as e:
                            st.error(f"Erro ao criar visualização: {str(e)}")
                    else:
                        st.warning("Os dados não têm colunas suficientes para visualização.")
                else:
                    st.info("Execute a consulta para visualizar os dados")
    else:
        st.info("👈 Conecte ao banco ou ative o modo Demo para começar")
        
        st.header("📌 Como funciona")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1️⃣ Configuração\nConfigurar API Vanna.ai e conexão com o banco de dados.")
        with col2:
            st.markdown("### 2️⃣ Pergunte\nFaça perguntas complexas em linguagem natural sobre seus dados.")
        with col3:
            st.markdown("### 3️⃣ Analise\nVisualize os resultados com gráficos interativos personalizados.")
    
    # Rodapé
    st.divider()
    st.markdown("DataTalk com Vanna.ai © 2025 - Consulta avançada de banco de dados por linguagem natural")
    
    # Status do Vanna.ai
    st.sidebar.divider()
    if VANNA_AVAILABLE:
        if st.session_state.vanna_client:
            st.sidebar.success("✅ Vanna.ai: Conectado")
        else:
            st.sidebar.info("ℹ️ Vanna.ai: Disponível (Não configurado)")
    else:
        st.sidebar.warning("⚠️ Vanna.ai: Indisponível (Modo Demo ativo)")

# Iniciar o aplicativo
if __name__ == "__main__":
    main()
