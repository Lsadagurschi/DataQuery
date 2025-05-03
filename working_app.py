import streamlit as st
import pandas as pd
import time

# Configuração da página
st.set_page_config(
    page_title="DataTalk - Consulta SQL por Linguagem Natural", 
    page_icon="💬", 
    layout="wide"
)

# Inicializar estados da sessão
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False
if 'is_demo' not in st.session_state:
    st.session_state.is_demo = False
if 'current_sql' not in st.session_state:
    st.session_state.current_sql = None
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Função para exibir o cabeçalho
def display_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("💬")  # Emoji como logo
    with col2:
        st.title("DataTalk")
        st.write("Consulte seu banco de dados usando linguagem natural")
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
                st.rerun()  # Corrigido: experimental_rerun → rerun
            else:
                st.error("Usuário ou senha inválidos")

# Função para simular geração de SQL
def generate_sql(query):
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

# Função para simular execução de SQL
def execute_sql(sql):
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
        st.header("🔗 Configuração do Banco")
        
        db_type = st.selectbox(
            "Tipo de Banco de Dados",
            ["PostgreSQL", "MySQL", "SQL Server"],
            index=0
        )
        
        host = st.text_input("Host", value="localhost")
        port = st.text_input("Porta", value="5432")
        database = st.text_input("Nome do Banco", value="neondb")
        username = st.text_input("Usuário", value="postgres")
        password = st.text_input("Senha", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Conectar"):
                st.session_state.is_connected = True
                st.session_state.is_demo = False
                st.success("Conectado!")
        
        with col2:
            if st.button("Modo Demo"):
                st.session_state.is_demo = True
                st.success("Demo ativado!")
        
        if st.session_state.is_connected:
            st.info(f"Conectado a {database} em {host}")
        
        if st.session_state.query_history:
            st.header("📜 Histórico")
            for i, query in enumerate(st.session_state.query_history[-3:]):
                with st.expander(f"Consulta {i+1}"):
                    st.code(query, language="sql")
        
        if st.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()  # Corrigido: experimental_rerun → rerun
    
    # Área principal
    if st.session_state.is_connected or st.session_state.is_demo:
        st.header("💬 Faça sua pergunta")
        
        query = st.text_area("O que você gostaria de saber?", 
                            placeholder="Ex: Quais são os 5 produtos mais vendidos?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Gerar SQL"):
                if query:
                    sql = generate_sql(query)
                    st.session_state.current_sql = sql
                    st.session_state.query = query
                    st.success("SQL gerado!")
        
        with col2:
            if st.button("Executar") and st.session_state.current_sql:
                results = execute_sql(st.session_state.current_sql)
                st.session_state.current_results = results
                if st.session_state.current_sql not in st.session_state.query_history:
                    st.session_state.query_history.append(st.session_state.current_sql)
                st.success("Consulta executada!")
        
        if st.session_state.current_sql:
            tabs = st.tabs(["📊 Resultados", "📝 SQL", "📈 Visualização"])
            
            with tabs[0]:
                if "current_results" in st.session_state and st.session_state.current_results is not None:
                    st.dataframe(st.session_state.current_results)
                else:
                    st.info("Execute a consulta para ver resultados")
            
            with tabs[1]:
                st.code(st.session_state.current_sql, language="sql")
            
            with tabs[2]:
                if "current_results" in st.session_state and st.session_state.current_results is not None:
                    df = st.session_state.current_results
                    if len(df.columns) >= 2:
                        x_col = df.columns[0]
                        y_col = df.columns[1] if len(df.columns) > 1 and pd.api.types.is_numeric_dtype(df[df.columns[1]]) else df.columns[0]
                        
                        chart_type = st.selectbox("Tipo de gráfico", ["Barra", "Linha", "Pizza"])
                        
                        if chart_type == "Barra":
                            st.bar_chart(df.set_index(x_col))
                        elif chart_type == "Linha":
                            st.line_chart(df.set_index(x_col))
                        else:
                            # Para Pizza, precisamos de um valor numérico
                            try:
                                import plotly.express as px
                                # Encontrar coluna numérica
                                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                                if numeric_cols:
                                    numeric_col = numeric_cols[0]
                                    fig = px.pie(df, names=x_col, values=numeric_col)
                                    st.plotly_chart(fig)
                                else:
                                    st.error("Não há colunas numéricas para criar gráfico de pizza")
                            except Exception as e:
                                st.error(f"Erro ao criar gráfico: {str(e)}")
                    else:
                        st.warning("Os dados não têm colunas suficientes para visualização.")
                else:
                    st.info("Execute a consulta para visualizar os dados")
    else:
        st.info("👈 Conecte ao banco ou ative o modo Demo para começar")
        
        st.header("📌 Como funciona")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1️⃣ Conecte-se\nConfiguração do banco no painel lateral.")
        with col2:
            st.markdown("### 2️⃣ Pergunte\nFaça perguntas em português sobre seus dados.")
        with col3:
            st.markdown("### 3️⃣ Analise\nVisualização interativa dos resultados.")
    
    # Rodapé
    st.divider()
    st.write("DataTalk © 2025 - Consulta de banco de dados por linguagem natural")

# Iniciar o aplicativo
if __name__ == "__main__":
    main()
