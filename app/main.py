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
from nlp_engine import natural_to_sql, validate_query, improve_model
from visualizations import create_visualization, export_visualization
from utils import save_query, get_history, add_to_gold_list, get_gold_list

# Configuração da página
st.set_page_config(
    page_title="NeoQuery AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Carregamento do CSS personalizado
def load_css():
    with open('static/css/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Função para exibir o logo
def display_logo():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # st.image('static/images/logo.png', width=300)

# Função principal para a página inicial
def main_page():
    display_logo()
    
    st.markdown("""
    # Bem-vindo ao NeoQuery AI
    
    Consulte seus dados em linguagem natural e obtenha insights poderosos sem precisar escrever uma linha de SQL.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ## Como funciona
        1. Conecte seu banco de dados
        2. Digite sua pergunta em linguagem natural
        3. Receba resultados instantâneos com visualizações
        4. Salve e compartilhe seus insights
        """)
    
    with col2:
        st.video('static/videos/demo.mp4')
    
    st.markdown("---")
    
    st.markdown("""
    ## Planos
    
    Escolha o plano que melhor atende às necessidades da sua empresa:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### Básico
        **R$199/mês**
        - Até 3 usuários
        - 100 consultas/mês
        - 1 conexão de banco de dados
        - Suporte por e-mail
        """)
        st.button("Assinar Plano Básico", key="basic_plan")
    
    with col2:
        st.markdown("""
        ### Profissional
        **R$499/mês**
        - Até 10 usuários
        - 500 consultas/mês
        - 3 conexões de banco de dados
        - Suporte prioritário
        - Exportação em múltiplos formatos
        """)
        st.button("Assinar Plano Profissional", key="pro_plan", type="primary")
    
    with col3:
        st.markdown("""
        ### Empresarial
        **R$999/mês**
        - Usuários ilimitados
        - Consultas ilimitadas
        - Conexões ilimitadas
        - Suporte 24/7
        - API avançada
        - Treinamento personalizado
        """)
        st.button("Assinar Plano Empresarial", key="enterprise_plan")

# Função para a página de login
def login_page():
    display_logo()
    
    st.markdown("## Login")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")
            
            if submit_button:
                if authenticate_user(email, password):
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.experimental_rerun()
                else:
                    st.error("E-mail ou senha inválidos!")
    
    with col2:
        st.markdown("""
        ### Novo por aqui?
        
        Crie uma conta e comece seu período de teste gratuito de 14 dias.
        
        Nenhum cartão de crédito necessário.
        """)
        
        if st.button("Criar uma conta"):
            st.session_state.page = "signup"
            st.experimental_rerun()

# Função para a página de cadastro
def signup_page():
    display_logo()
    
    st.markdown("## Criar uma conta")
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome completo")
            email = st.text_input("E-mail")
            
        with col2:
            password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar senha", type="password")
        
        company = st.text_input("Empresa")
        
        terms = st.checkbox("Eu concordo com os Termos de Serviço e Política de Privacidade")
        
        submit_button = st.form_submit_button("Criar conta")
        
        if submit_button:
            if password != confirm_password:
                st.error("As senhas não conferem!")
            elif not terms:
                st.error("Você precisa concordar com os termos para criar uma conta.")
            else:
                if create_user(name, email, password, company):
                    st.success("Conta criada com sucesso! Faça login para continuar.")
                    st.session_state.page = "login"
                    st.experimental_rerun()
                else:
                    st.error("Este e-mail já está em uso!")

# Função para a página do dashboard
def dashboard_page():
    st.sidebar.title("NeoQuery AI")
    
    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Conexões de Banco", "Histórico", "Consultas Salvas", "Configurações"]
    )
    
    if menu == "Dashboard":
        st.title("Dashboard")
        
        # Área de conexão do banco de dados
        if "db_connected" not in st.session_state:
            st.session_state.db_connected = False
            
        if not st.session_state.db_connected:
            st.markdown("## Conecte seu banco de dados")
            
            with st.form("db_connection_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    db_type = st.selectbox("Tipo de banco de dados", ["PostgreSQL", "MySQL", "SQL Server", "Oracle"])
                    host = st.text_input("Host", value="db.neon.tech")
                    port = st.text_input("Porta", value="5432")
                
                with col2:
                    database = st.text_input("Nome do banco")
                    username = st.text_input("Usuário")
                    password = st.text_input("Senha", type="password")
                
                connect_button = st.form_submit_button("Conectar")
                
                if connect_button:
                    if test_connection(db_type, host, port, database, username, password):
                        st.session_state.db_connected = True
                        st.session_state.db_info = {
                            "type": db_type,
                            "host": host,
                            "port": port,
                            "database": database,
                            "username": username,
                            "password": password
                        }
                        st.success("Conexão estabelecida com sucesso!")
                        st.experimental_rerun()
                    else:
                        st.error("Não foi possível conectar ao banco de dados. Verifique as informações e tente novamente.")
        
        else:
            # Área de consulta em linguagem natural
            st.markdown("## O que você quer saber sobre seus dados?")
            
            query = st.text_area(
                "Digite sua pergunta em linguagem natural",
                placeholder="Ex: Mostre-me o total de vendas por região nos últimos 3 meses",
                height=100
            )
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                pass
            
            with col2:
                query_button = st.button("Consultar", type="primary", use_container_width=True)
            
            if query_button and query:
                with st.spinner("Processando sua consulta..."):
                    # Converter linguagem natural para SQL
                    sql_query = natural_to_sql(query, st.session_state.db_info)
                    
                    # Verificar e validar a query gerada
                    is_valid, message = validate_query(sql_query, st.session_state.db_info)
                    
                    if is_valid:
                        # Executar a consulta
                        result_df = execute_query(sql_query, st.session_state.db_info)
                        
                        # Exibir tabs para os diferentes tipos de visualização
                        tabs = st.tabs(["SQL Gerado", "Tabela de Resultados", "Gráfico", "Dashboard"])
                        
                        with tabs[0]:
                            st.code(sql_query, language="sql")
                            st.download_button(
                                "Baixar SQL", 
                                sql_query, 
                                file_name="consulta.sql",
                                mime="text/plain"
                            )
                        
                        with tabs[1]:
                            st.dataframe(result_df, use_container_width=True)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("Exportar para CSV"):
                                    csv = result_df.to_csv(index=False)
                                    st.download_button(
                                        "Baixar CSV",
                                        csv,
                                        file_name="resultados.csv",
                                        mime="text/csv"
                                    )
                            
                            with col2:
                                if st.button("Salvar Consulta"):
                                    save_query(query, sql_query, st.session_state.user_email)
                                    st.success("Consulta salva com sucesso!")
                        
                        with tabs[2]:
                            if not result_df.empty:
                                # Determinar automaticamente o tipo de gráfico adequado
                                viz_container = st.container()
                                
                                with viz_container:
                                    if len(result_df.columns) >= 2:
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            x_axis = st.selectbox("Eixo X", options=result_df.columns)
                                        
                                        with col2:
                                            y_axis = st.selectbox("Eixo Y", options=result_df.select_dtypes(include=['number']).columns)
                                        
                                        chart_type = st.selectbox(
                                            "Tipo de Gráfico",
                                            ["Barras", "Linhas", "Dispersão", "Pizza"]
                                        )
                                        
                                        if chart_type == "Barras":
                                            fig = px.bar(result_df, x=x_axis, y=y_axis, title=f"{y_axis} por {x_axis}")
                                        elif chart_type == "Linhas":
                                            fig = px.line(result_df, x=x_axis, y=y_axis, title=f"{y_axis} por {x_axis}")
                                        elif chart_type == "Dispersão":
                                            fig = px.scatter(result_df, x=x_axis, y=y_axis, title=f"{y_axis} por {x_axis}")
                                        elif chart_type == "Pizza":
                                            fig = px.pie(result_df, names=x_axis, values=y_axis, title=f"{y_axis} por {x_axis}")
                                        
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        if st.button("Exportar Gráfico (PDF)"):
                                            # Função para exportar o gráfico
                                            export_visualization(fig, f"grafico_{x_axis}_{y_axis}.pdf")
                                            st.success("Gráfico exportado com sucesso!")
                                    else:
                                        st.warning("É necessário ter pelo menos duas colunas para criar um gráfico.")
                        
                        with tabs[3]:
                            st.markdown("## Dashboard")
                            st.info("Funcionalidade em desenvolvimento. Em breve você poderá criar dashboards personalizados com suas consultas favoritas!")
                        
                        # Área de feedback
                        st.markdown("---")
                        st.markdown("## Esta consulta atendeu suas expectativas?")
                        
                        col1, col2, col3 = st.columns([1, 1, 3])
                        
                        with col1:
                            if st.button("👍 Sim"):
                                add_to_gold_list(query, sql_query, st.session_state.user_email)
                                improve_model(query, sql_query, feedback="positive")
                                st.success("Obrigado pelo feedback! Esta consulta foi adicionada à lista de referência.")
                        
                        with col2:
                            if st.button("👎 Não"):
                                st.text_area("Como podemos melhorar?", key="feedback_text")
                                if st.button("Enviar feedback"):
                                    improve_model(query, sql_query, feedback="negative", details=st.session_state.feedback_text)
                                    st.success("Obrigado pelo feedback! Vamos trabalhar para melhorar.")
                    
                    else:
                        st.error(f"Erro na consulta gerada: {message}")
            
            # Se não houver consulta ativa, mostrar sugestões
            if "result_df" not in locals():
                st.markdown("### Sugestões de consultas:")
                
                suggestions = [
                    "Mostre o total de vendas mensais do último trimestre",
                    "Quais são os 5 produtos mais vendidos?",
                    "Compare o desempenho das regiões Sul e Sudeste"
                ]
                
                for suggestion in suggestions:
                    if st.button(suggestion, key=suggestion):
                        # Preencher a área de texto com a sugestão
                        st.session_state.query = suggestion
                        st.experimental_rerun()
                
                # Exibir histórico recente
                st.markdown("### Consultas recentes:")
                recent_queries = get_history(st.session_state.user_email, limit=3)
                
                for i, (timestamp, query_text, sql) in enumerate(recent_queries):
                    with st.expander(f"{query_text[:50]}..." if len(query_text) > 50 else query_text):
                        st.markdown(f"**Data:** {timestamp}")
                        st.code(sql, language="sql")
                        if st.button("Executar novamente", key=f"rerun_{i}"):
                            # Preencher a área de texto com a consulta histórica
                            st.session_state.query = query_text
                            st.experimental_rerun()
    
    elif menu == "Conexões de Banco":
        st.title("Conexões de Banco de Dados")
        
        st.markdown("""
        Gerencie suas conexões de banco de dados aqui. Você pode adicionar novas conexões, 
        testar conexões existentes e gerenciar permissões.
        """)
        
        # Listar conexões existentes
        st.markdown("## Conexões configuradas")
        
        # Exemplo de conexões para demonstração
        connections = [
            {"name": "Banco Principal", "type": "PostgreSQL", "host": "db.neon.tech", "status": "Ativo"},
            {"name": "Banco de Testes", "type": "PostgreSQL", "host": "test-db.neon.tech", "status": "Inativo"}
        ]
        
        for conn in connections:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{conn['name']}**")
            
            with col2:
                st.markdown(conn['type'])
            
            with col3:
                if conn['status'] == "Ativo":
                    st.markdown("🟢 Ativo")
                else:
                    st.markdown("🔴 Inativo")
            
            with col4:
                st.button("Gerenciar", key=f"manage_{conn['name']}")
        
        st.markdown("---")
        
        # Formulário para adicionar nova conexão
        st.markdown("## Adicionar nova conexão")
        
        with st.form("add_connection_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                conn_name = st.text_input("Nome da conexão")
                db_type = st.selectbox("Tipo de banco de dados", ["PostgreSQL", "MySQL", "SQL Server", "Oracle"])
                host = st.text_input("Host")
                port = st.text_input("Porta")
            
            with col2:
                database = st.text_input("Nome do banco")
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                ssl_required = st.checkbox("Requer SSL")
            
            test_conn_button = st.form_submit_button("Testar conexão")
            
            if test_conn_button:
                with st.spinner("Testando conexão..."):
                    # Simulando um teste de conexão
                    st.success("Conexão estabelecida com sucesso!")
    
    elif menu == "Histórico":
        st.title("Histórico de Consultas")
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            date_range = st.date_input("Período", [])
        
        with col2:
            search_term = st.text_input("Pesquisar", placeholder="Digite para buscar...")
        
        # Lista de histórico de consultas
        st.markdown("## Consultas realizadas")
        
        # Exemplo de histórico para demonstração
        history = [
            {"date": "2025-05-05 14:32", "query": "Mostre o total de vendas por região", "status": "Sucesso"},
            {"date": "2025-05-04 10:15", "query": "Quais são os clientes que não fizeram compras nos últimos 30 dias?", "status": "Sucesso"},
            {"date": "2025-05-03 16:22", "query": "Liste os produtos com estoque abaixo do mínimo", "status": "Erro"}
        ]
        
        for item in history:
            with st.expander(f"{item['date']} - {item['query']}"):
                st.markdown(f"**Status:** {item['status']}")
                st.markdown("**Consulta em linguagem natural:**")
                st.markdown(item['query'])
                
                st.markdown("**SQL gerado:**")
                st.code("SELECT * FROM tabela WHERE condição;", language="sql")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    st.button("Executar novamente", key=f"rerun_{item['date']}")
                
                with col2:
                    st.button("Salvar consulta", key=f"save_{item['date']}")
    
    elif menu == "Consultas Salvas":
        st.title("Consultas Salvas")
        
        # Categorias
        categories = st.multiselect("Categorias", ["Vendas", "Estoque", "Clientes", "Financeiro"])
        
        # Lista de consultas salvas
        st.markdown("## Minhas consultas")
        
        # Exemplo de consultas salvas para demonstração
        saved_queries = [
            {"name": "Vendas por região", "category": "Vendas", "created": "2025-04-25", "starred": True},
            {"name": "Produtos com estoque crítico", "category": "Estoque", "created": "2025-04-30", "starred": False}
        ]
        
        for query in saved_queries:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                title = query['name']
                if query['starred']:
                    title = f"⭐ {title}"
                st.markdown(f"**{title}**")
            
            with col2:
                st.markdown(query['category'])
            
            with col3:
                st.markdown(query['created'])
            
            with col4:
                st.button("Executar", key=f"run_{query['name']}")
        
        st.markdown("---")
        
        # Gold List (consultas de referência)
        st.markdown("## Lista de referência")
        st.markdown("Consultas validadas que ajudam a melhorar o sistema")
        
        # Exemplo de gold list para demonstração
        gold_queries = [
            {"query": "Mostre o faturamento mensal do último ano", "accuracy": "98%"},
            {"query": "Liste os 10 clientes que mais compraram no último trimestre", "accuracy": "95%"}
        ]
        
        for i, query in enumerate(gold_queries):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{query['query']}**")
            
            with col2:
                st.markdown(f"Precisão: {query['accuracy']}")
            
            with col3:
                st.button("Ver SQL", key=f"sql_{i}")
    
    elif menu == "Configurações":
        st.title("Configurações")
        
        tabs = st.tabs(["Perfil", "Preferências", "Integrações", "LGPD"])
        
        with tabs[0]:
            st.markdown("## Dados do perfil")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Nome", value="Usuário Exemplo")
                st.text_input("E-mail", value="usuario@exemplo.com")
                st.text_input("Empresa", value="Empresa Exemplo")
            
            with col2:
                st.selectbox("Plano atual", ["Básico", "Profissional", "Empresarial"])
                st.text_input("Data de renovação", value="06/06/2025", disabled=True)
            
            st.button("Salvar alterações")
        
        with tabs[1]:
            st.markdown("## Preferências do sistema")
            
            st.selectbox("Tema", ["Claro", "Escuro", "Sistema"])
            st.selectbox("Idioma", ["Português", "English", "Español"])
            st.selectbox("Formato de data padrão", ["DD/MM/AAAA", "MM/DD/AAAA", "AAAA-MM-DD"])
            
            st.checkbox("Salvar consultas automaticamente")
            st.checkbox("Mostrar SQL gerado por padrão")
            
            st.button("Aplicar configurações")
        
        with tabs[2]:
            st.markdown("## Integrações")
            
            st.markdown("### Conecte com outras ferramentas")
            
            integrations = [
                {"name": "Tableau", "status": "Não conectado", "icon": "📊"},
                {"name": "Power BI", "status": "Não conectado", "icon": "📈"},
                {"name": "Slack", "status": "Conectado", "icon": "💬"}
            ]
            
            for integration in integrations:
                col1, col2, col3 = st.columns([1, 2, 2])
                
                with col1:
                    st.markdown(f"### {integration['icon']}")
                
                with col2:
                    st.markdown(f"**{integration['name']}**")
                
                with col3:
                    if integration['status'] == "Conectado":
                        st.button("Desconectar", key=f"disconnect_{integration['name']}")
                    else:
                        st.button("Conectar", key=f"connect_{integration['name']}")
        
        with tabs[3]:
            st.markdown("## Privacidade e LGPD")
            
            st.markdown("""
            ### Tratamento de Dados
            
            O NeoQuery AI está em conformidade com a Lei Geral de Proteção de Dados (LGPD).
            
            - Seus dados pessoais são usados apenas para fornecer o serviço contratado
            - Seus dados de consulta são usados para melhorar o sistema de NLP
            - Não compartilhamos seus dados com terceiros sem consentimento
            """)
            
            st.markdown("### Opções de privacidade")
            
            st.checkbox("Permitir uso de consultas para aprimoramento do sistema", value=True)
            st.checkbox("Receber e-mails sobre atualizações e novos recursos", value=True)
            
            if st.button("Solicitar exclusão de dados"):
                st.info("Um e-mail será enviado com instruções para solicitar a exclusão dos seus dados.")
            
            st.markdown("### Política de Privacidade completa")
            st.download_button(
                "Baixar Política de Privacidade (PDF)",
                "conteúdo do pdf",
                file_name="politica_privacidade.pdf"
            )
    
    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"Usuário: {st.session_state.user_email}")
    
    if st.sidebar.button("Sair"):
        st.session_state.authenticated = False
        st.session_state.page = "login"
        st.experimental_rerun()

# Controle de navegação
if "page" not in st.session_state:
    st.session_state.page = "main"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Navegação principal
if st.session_state.authenticated:
    dashboard_page()
else:
    if st.session_state.page == "main":
        main_page()
        
        col1, col2 = st.columns([4, 1])
        
        with col2:
            if st.button("Área do usuário", type="primary"):
                st.session_state.page = "login"
                st.experimental_rerun()
    
    elif st.session_state.page == "login":
        login_page()
        
        if st.button("← Voltar"):
            st.session_state.page = "main"
            st.experimental_rerun()
    
    elif st.session_state.page == "signup":
        signup_page()
        
        if st.button("← Voltar para login"):
            st.session_state.page = "login"
            st.experimental_rerun()
