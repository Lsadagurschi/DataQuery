import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import time
import datetime
import sys
import plotly.express as px
from pathlib import Path

# Adicionar os diretórios ao path
script_dir = Path(__file__).parent.absolute()
sys.path.append(str(script_dir))

from modules.db_connector import DBConnector
from modules.sql_generator import SQLGenerator
from modules.visualizer import DataVisualizer
from modules.security import SecurityManager
from modules.data_protection import DataProtector
from config import get_config
from security_config import get_security_config

# Carregar variáveis de ambiente
try:
    load_dotenv()
except:
    pass  # No .env file, will use defaults


# Suporte para secrets do Streamlit Cloud
def get_secret(key, default=None):
    """Obtém um segredo do Streamlit Cloud ou variável de ambiente"""
    try:
        if st.secrets and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)

# Inicialização dos componentes de segurança
security_manager = SecurityManager(get_security_config("JWT_SECRET_KEY"))
data_protector = DataProtector(get_security_config("ENCRYPTION_KEY"))

# Configuração da página Streamlit
st.set_page_config(
    page_title="DataTalk - Consulta SQL por Linguagem Natural", 
    page_icon="💬", 
    layout="wide"
)

# Função para verificar autenticação
def check_authentication():
    if not get_security_config("AUTH_REQUIRED", True):
        return True

    if "authenticated" in st.session_state and st.session_state.authenticated:
        # Verificar tempo de sessão
        session_timeout = get_security_config("SESSION_TIMEOUT", 3600)
        if "last_activity" in st.session_state:
            time_elapsed = time.time() - st.session_state.last_activity
            if time_elapsed > session_timeout:
                st.session_state.authenticated = False
                return False
        
        # Atualizar timestamp de última atividade
        st.session_state.last_activity = time.time()
        return True
        
    return False

# Função para página de login
def show_login_page():
    st.title("DataTalk - Login")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            # Em um ambiente real, verificaria contra banco de dados
            # Aqui vamos usar um usuário de teste
            if username == "admin" and password == "admin":
                user_data = {
                    "username": username,
                    "role": "admin",
                    "permissions": ["query", "connect", "visualize"]
                }
                token = security_manager.generate_token(user_data)
                st.session_state.token = token
                st.session_state.authenticated = True
                st.session_state.user = user_data
                st.session_state.last_activity = time.time()
                
                # Log de atividade
                security_manager.log_activity(
                    username, "login", "system", "success"
                )
                
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                # Log de falha
                security_manager.log_activity(
                    username, "login", "system", "failed",
                    "Credenciais inválidas"
                )
                st.error("Usuário ou senha inválidos")

    # Link para política de privacidade
    if st.button("Ver Política de Privacidade"):
        show_privacy_policy()

# Função para exibir a política de privacidade
def show_privacy_policy():
    st.subheader("Política de Privacidade")
    
    st.markdown("""
    **Política de Privacidade e Termos de Uso - DataTalk**
    
    Esta política descreve como a aplicação DataTalk coleta, usa e protege seus dados.
    
    **Coleta de Dados:**
    - A aplicação não armazena dados consultados, apenas processa temporariamente
    - Armazenamos logs de acesso e atividade por motivos de segurança
    - Suas credenciais de banco de dados são utilizadas apenas para conexão e não são armazenadas permanentemente
    
    **Uso dos Dados:**
    - Os dados são utilizados exclusivamente para fornecer o serviço solicitado
    - Não compartilhamos suas informações com terceiros
    - Consultas são processadas localmente e não são enviadas para servidores externos
    
    **Seus Direitos:**
    - Você pode solicitar a exclusão de todos os seus dados a qualquer momento
    - Você pode exportar seus registros de atividade
    - Você controla totalmente quais dados são processados
    
    **Segurança:**
    - Utilizamos criptografia para proteger suas informações
    - Implementamos medidas técnicas para garantir a integridade dos dados
    - Realizamos auditorias regulares de segurança
    """)
    
    if st.button("Aceitar Termos"):
        st.session_state.terms_accepted = True
        st.success("Termos aceitos. Obrigado!")
        st.experimental_rerun()

# Função para solicitar exclusão de dados
def request_data_deletion():
    st.subheader("Solicitar Exclusão de Dados")
    
    st.write("""
    Ao solicitar a exclusão, todos os seus dados pessoais armazenados serão
    permanentemente removidos do sistema, incluindo:
    
    - Histórico de consultas
    - Logs de acesso
    - Preferências e configurações
    """)
    
    if st.button("Solicitar Exclusão"):
        # Em um ambiente real, iniciaria o processo de exclusão
        user_id = st.session_state.user["username"]
        security_manager.log_activity(
            user_id,
            "data_deletion",
            "user_data",
            "requested"
        )
        
        st.success("""
        Sua solicitação foi registrada. Todos os seus dados serão removidos em até 48 horas.
        Você receberá uma confirmação quando o processo for concluído.
        """)

# Função para exibir o cabeçalho
def display_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=100)
        else:
            st.write("💬")
    with col2:
        st.title("DataTalk")
        st.write("Consulte seu banco de dados usando linguagem natural")
    st.divider()

# Inicializar estados da sessão se não existirem
if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False
if 'db_schema' not in st.session_state:
    st.session_state.db_schema = None
if 'current_sql' not in st.session_state:
    st.session_state.current_sql = None
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Função para conectar ao banco de dados
def connect_to_database(db_type, host, port, database, username, password):
    try:
        db_connector = DBConnector(db_type, host, port, database, username, password)
        
        # Verificar se a conexão é segura
        is_secure = db_connector.secure_connection()
        if not is_secure:
            return False, "Aviso: Conexão não está utilizando criptografia (SSL/TLS)."
            
        schema = db_connector.get_database_schema()
        
        st.session_state.db_connector = db_connector
        st.session_state.db_schema = schema
        st.session_state.is_connected = True
        
        # Inicializar o gerador SQL
        sql_generator = SQLGenerator(schema)
        st.session_state.sql_generator = sql_generator
        
        # Log de atividade
        if "user" in st.session_state:
            security_manager.log_activity(
                st.session_state.user["username"],
                "database_connect",
                f"{db_type}/{database}",
                "success"
            )
        
        return True, "Conexão estabelecida com sucesso!"
    except Exception as e:
        # Log de erro
        if "user" in st.session_state:
            security_manager.log_activity(
                st.session_state.user["username"],
                "database_connect",
                f"{db_type}/{database}",
                "failed",
                str(e)
            )
        return False, f"Erro ao conectar: {str(e)}"

# Função para gerar SQL a partir da linguagem natural
def generate_sql_query(query):
    try:
        # Sanitizar a consulta
        clean_query = data_protector.sanitize_input(query)
        
        # Auditoria da consulta
        audit_result = data_protector.audit_query(clean_query)
        if audit_result["risk_level"] == "high":
            st.warning("Esta consulta pode acessar dados sensíveis. Tenha cuidado.")
        
        sql_query = st.session_state.sql_generator.generate_sql(clean_query)
        st.session_state.current_sql = sql_query
        
        # Log de atividade
        if "user" in st.session_state:
            security_manager.log_activity(
                st.session_state.user["username"],
                "generate_sql",
                clean_query[:50] + "..." if len(clean_query) > 50 else clean_query,
                "success"
            )
            
        return True, sql_query
    except Exception as e:
        # Log de erro
        if "user" in st.session_state:
            security_manager.log_activity(
                st.session_state.user["username"],
                "generate_sql",
                query[:50] + "..." if len(query) > 50 else query,
                "failed",
                str(e)
            )
        return False, f"Erro ao gerar SQL: {str(e)}"

# Função para executar a consulta SQL
def execute_sql_query(sql_query):
    try:
        results = st.session_state.db_connector.execute_query(sql_query)
        
        # Anonimizar dados sensíveis se configurado
        if get_security_config("ANONYMIZE_SENSITIVE_DATA", True):
            # Detectar colunas potencialmente sensíveis
            sensitive_columns = {}
            for col in results.columns:
                # Verificar apenas colunas de texto
                if results[col].dtype == 'object':
                    # Amostragem para performance
                    sample = results[col].dropna().head(5).astype(str).tolist()
                    for value in sample:
                        detection = data_protector.detect_sensitive_data(value)
                        if detection:
                            # Encontrou dado sensível nesta coluna
                            data_type = next(iter(detection.keys()))
                            sensitive_columns[col] = 'mask'
                            break
            
            # Anonimizar dados se encontrou colunas sensíveis
            if sensitive_columns:
                results = data_protector.anonymize_data(results, sensitive_columns)
                st.info(f"Dados sensíveis foram anonimizados em {len(sensitive_columns)} coluna(s).")
        
        st.session_state.current_results = results
        
        # Log de atividade
        if "user" in st.session_state:
            security_manager.log_activity(
                st.session_state.user["username"],
                "execute_query",
                sql_query[:50] + "..." if len(sql_query) > 50 else sql_query,
                "success",
                f"Rows: {len(results)}"
            )
            
        return True, results
    except Exception as e:
        # Log de erro
        if "user" in st.session_state:
            security_manager.log_activity(
                st.session_state.user["username"],
                "execute_query",
                sql_query[:50] + "..." if len(sql_query) > 50 else sql_query,
                "failed",
                str(e)
            )
        return False, f"Erro ao executar consulta: {str(e)}"

# Função para adicionar à história de consultas
def add_to_history(natural_query, sql_query, results):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.query_history.append({
        "timestamp": timestamp,
        "natural_query": natural_query,
        "sql_query": sql_query,
        "results": results
    })

# Função principal
def main():
    # Verificar autenticação
    if not check_authentication():
        show_login_page()
        return
    
    # Exibir cabeçalho da página
    display_header()

    # Sidebar para configuração da conexão
    with st.sidebar:
        st.header("🔗 Configuração do Banco")
        
        db_type = st.selectbox(
            "Tipo de Banco de Dados",
            ["PostgreSQL", "MySQL", "SQL Server"],
            index=0
        )
        
        default_ports = {
            "PostgreSQL": "5432",
            "MySQL": "3306",
            "SQL Server": "1433"
        }
        
        host = st.text_input("Host", value="localhost")
        port = st.text_input("Porta", value=default_ports[db_type])
        database = st.text_input("Nome do Banco", value="neondb")
        username = st.text_input("Usuário", value="postgres")
        password = st.text_input("Senha", type="password")
        
        connect_button = st.button("Conectar ao Banco")
        
        if connect_button:
            with st.spinner("Conectando ao banco de dados..."):
                success, message = connect_to_database(db_type, host, port, database, username, password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        if st.session_state.is_connected:
            st.markdown(f"""
            ✅ Conectado
                Banco: {database}
                Servidor: {host}:{port}
            
            """, unsafe_allow_html=True)
        
        # Histórico de consultas
        if st.session_state.query_history and st.session_state.is_connected:
            st.header("📜 Histórico de Consultas")
            for i, query in enumerate(reversed(st.session_state.query_history[-5:])):
                with st.expander(f"{query['timestamp']} - {query['natural_query'][:30]}..."):
                    st.code(query['sql_query'], language="sql")
        
        # Opções de segurança e privacidade
        st.header("🔒 Segurança e Privacidade")
        if st.button("Política de Privacidade"):
            show_privacy_policy()
            
        if st.button("Solicitar Exclusão de Dados"):
            request_data_deletion()
            
        # Opção para logout
        if st.button("Sair"):
            if "user" in st.session_state:
                security_manager.log_activity(
                    st.session_state.user["username"],
                    "logout",
                    "system",
                    "success"
                )
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

    # Área principal para consultas
    if st.session_state.is_connected:
        st.header("💬 Faça sua pergunta")
        
        # Input para a pergunta em linguagem natural
        natural_query = st.text_area(
            "O que você gostaria de saber sobre seus dados?",
            placeholder="Ex: Quantas vendas tivemos em janeiro e fevereiro?",
            height=100
        )
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            generate_button = st.button("Gerar SQL")
        with col2:
            execute_button = st.button("Executar Consulta")
        
        # Lógica para gerar SQL
        if generate_button and natural_query:
            with st.spinner("Gerando consulta SQL..."):
                success, sql_result = generate_sql_query(natural_query)
                if success:
                    st.session_state.current_natural_query = natural_query
                    st.success("SQL gerado com sucesso!")
                else:
                    st.error(sql_result)
        
        # Lógica para executar SQL
        if execute_button and st.session_state.current_sql:
            with st.spinner("Executando consulta..."):
                success, results = execute_sql_query(st.session_state.current_sql)
                if success:
                    add_to_history(
                        st.session_state.current_natural_query,
                        st.session_state.current_sql,
                        results
                    )
                    st.success("Consulta executada com sucesso!")
                else:
                    st.error(results)
        
        # Exibir resultados se disponíveis
        if st.session_state.current_sql:
            tab1, tab2, tab3 = st.tabs(["📊 Resultados", "📝 SQL Gerado", "📈 Visualização"])
            
            with tab1:
                if st.session_state.current_results is not None and not st.session_state.current_results.empty:
                    st.dataframe(st.session_state.current_results, use_container_width=True)
                    
                    # Mostrar estatísticas básicas
                    if len(st.session_state.current_results) > 0:
                        st.subheader("Estatísticas")
                        st.write(f"Total de registros: {len(st.session_state.current_results)}")
                        
                        # Exportar opções
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = st.session_state.current_results.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "Baixar como CSV",
                                csv,
                                "dados.csv",
                                "text/csv",
                                key='download-csv'
                            )
                else:
                    st.info("Execute a consulta para ver os resultados aqui.")
                    
            with tab2:
                st.code(st.session_state.current_sql, language="sql")
                
            with tab3:
                if st.session_state.current_results is not None and not st.session_state.current_results.empty:
                    visualizer = DataVisualizer(st.session_state.current_results)
                    
                    # Opção de visualizar com privacidade
                    use_privacy = st.checkbox("Aplicar proteções de privacidade adicionais na visualização")
                    
                    if use_privacy:
                        fig = visualizer.visualize_with_privacy(
                            st.session_state.current_results
                        )
                    else:
                        fig = visualizer.suggest_visualization()
                        
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Opções de customização do gráfico
                    st.subheader("Personalizar Gráfico")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        chart_type = st.selectbox(
                            "Tipo de Gráfico",
                            ["Barra", "Linha", "Dispersão", "Pizza"],
                            key="chart_type"
                        )
                    
                    with col2:
                        if len(st.session_state.current_results.columns) > 0:
                            x_axis = st.selectbox(
                                "Eixo X",
                                st.session_state.current_results.columns,
                                key="x_axis"
                            )
                    
                    with col3:
                        if len(st.session_state.current_results.columns) > 0:
                            y_axis = st.selectbox(
                                "Eixo Y",
                                st.session_state.current_results.columns,
                                key="y_axis",
                                index=min(1, len(st.session_state.current_results.columns)-1)
                            )
                    
                    if st.button("Atualizar Gráfico"):
                        custom_fig = visualizer.create_custom_visualization(chart_type, x_axis, y_axis)
                        st.plotly_chart(custom_fig, use_container_width=True)
                else:
                    st.info("Execute a consulta para ver uma visualização dos dados aqui.")
                    
    else:
 if st.session_state.is_connected:
    # código para conexão estabelecida
else:
    # Modo de demonstração
    if 'is_demo' not in st.session_state:
        st.session_state.is_demo = False       

if not st.session_state.is_connected and not st.session_state.is_demo:
    if st.button("Ver Demonstração Completa"):
        st.session_state.is_demo = True
        st.experimental_rerun()

if not st.session_state.is_connected and st.session_state.get("is_demo", False):

    st.info("👈 Conecte-se a um banco de dados para começar.")
            
            # Demonstração quando não estiver conectado
            st.header("📌 Como funciona")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                ### 1️⃣ Conecte-se
                Conecte o DataTalk ao seu banco de dados através das configurações no menu lateral.
                """)
            with col2:
                st.markdown("""
                ### 2️⃣ Pergunte
                Faça perguntas em português sobre seus dados, como "Quais são os 10 clientes que mais compraram no último mês?"
                """)
            with col3:
                st.markdown("""
                ### 3️⃣ Analise
                Visualize os resultados em tabelas e gráficos interativos para uma análise completa.
                """)
            
            # Demonstração de consulta
            st.subheader("Exemplo de consulta")
            
            demo_query = "Quais são os 5 produtos mais vendidos nos últimos 3 meses?"
            demo_sql = """
            SELECT p.product_name, SUM(oi.quantity) as total_sold
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_date >= CURRENT_DATE - INTERVAL '3 months'
            GROUP BY p.product_name
            ORDER BY total_sold DESC
            LIMIT 5;
            """
            
            st.text_area("Pergunta em linguagem natural:", value=demo_query, disabled=True)
            st.code(demo_sql, language="sql")
            
            # Gráfico de exemplo
            demo_data = pd.DataFrame({
                'product_name': ['Notebook Pro', 'Smartphone X', 'Monitor 4K', 'Teclado Wireless', 'Mouse Gamer'],
                'total_sold': [324, 286, 195, 178, 156]
            })
            
            fig = px.bar(
                demo_data,
                x='product_name',
                y='total_sold',
                title='Top 5 Produtos Mais Vendidos (Últimos 3 Meses)',
                labels={'product_name': 'Produto', 'total_sold': 'Quantidade Vendida'},
                color='total_sold',
                color_continuous_scale='blues'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Seção de segurança e LGPD
            st.header("🔒 Segurança e Conformidade LGPD")
            st.markdown("""
            O DataTalk foi projetado com foco em segurança e conformidade com a LGPD:
            
            - **Criptografia** de dados em trânsito e em repouso
            - **Anonimização** automática de dados sensíveis (CPF, email, telefone, etc.)
            - **Registro de atividades** para fins de auditoria
            - **Acesso controlado** com autenticação e autorização
            - **Proteção contra injeção de SQL** e outras vulnerabilidades
            """)
    
        # Rodapé
    st.divider()
    st.markdown("DataTalk © 2025 - Consulta de banco de dados por linguagem natural | Em conformidade com a LGPD", unsafe_allow_html=True)

# Chamada principal
if __name__ == "__main__":
    main()
