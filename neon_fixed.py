import streamlit as st
import pandas as pd
import time
import os
import plotly.express as px
from sqlalchemy import create_engine, text

# Configuração da página
st.set_page_config(
    page_title="DataTalk - Futebol", 
    page_icon="⚽", 
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
if 'db_engine' not in st.session_state:
    st.session_state.db_engine = None

# Função para exibir o cabeçalho
def display_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("⚽")  # Emoji como logo
    with col2:
        st.title("DataTalk - Futebol")
        st.write("Consulte dados de futebol usando linguagem natural")
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

# Função para conectar ao banco de dados (CORRIGIDA para Neon)
def connect_to_database(host, port, database, username, password):
    try:
        # Corrigido com formato específico para o Neon
        # Importante: Host deve ser o endpoint completo do Neon!
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=require"
        
        # Exibir string de conexão (sem a senha)
        safe_connection = connection_string.replace(password, "********")
        st.info(f"Tentando conectar com: {safe_connection}")
        
        # Criar o engine do SQLAlchemy
        engine = create_engine(connection_string)
        
        # Testar conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            st.success(f"Teste de conexão bem-sucedido: {test_value}")
        
        st.session_state.db_engine = engine
        return True
    except Exception as e:
        st.error(f"Erro na conexão: {str(e)}")
        
        # Mostrar sugestões específicas para ajudar a resolver o problema
        st.warning("""
        **Dicas para solucionar o problema:**
        1. Verifique se o endereço do host está correto (deve ser algo como: `ep-name-12345.region.neon.tech`)
        2. Certifique-se de que está usando o nome de usuário e senha corretos
        3. Confirme se o banco de dados existe no Neon
        4. Verifique se o IP de onde está rodando o aplicativo não está bloqueado por firewalls
        """)
        
        return False

# Função para simular geração de SQL
def generate_sql(query):
    query_lower = query.lower()
    
    if "torcedores" in query_lower:
        return """
        SELECT nome, email, cidade, estado, data_nascimento
        FROM torcedores
        ORDER BY nome
        LIMIT 10;
        """
    elif "jogos" in query_lower or "partidas" in query_lower:
        return """
        SELECT j.jogo_id, tc.nome AS time_casa, tv.nome AS time_visitante, 
               j.data_hora, j.placar_casa, j.placar_visitante, j.publico_total,
               e.nome AS estadio
        FROM jogos j
        JOIN times tc ON j.time_casa_id = tc.time_id
        JOIN times tv ON j.time_visitante_id = tv.time_id
        JOIN estadios e ON j.estadio_id = e.estadio_id
        ORDER BY j.data_hora DESC
        LIMIT 10;
        """
    elif "ingressos" in query_lower or "vendidos" in query_lower:
        return """
        SELECT i.ingresso_id, t.nome AS torcedor, 
               tc.nome AS time_casa, tv.nome AS time_visitante,
               j.data_hora AS data_jogo, se.nome AS setor, i.preco
        FROM ingressos i
        JOIN torcedores t ON i.torcedor_id = t.torcedor_id
        JOIN jogos j ON i.jogo_id = j.jogo_id
        JOIN times tc ON j.time_casa_id = tc.time_id
        JOIN times tv ON j.time_visitante_id = tv.time_id
        JOIN setores_estadio se ON i.setor_id = se.setor_id
        ORDER BY j.data_hora DESC
        LIMIT 15;
        """
    elif "estadios" in query_lower:
        return """
        SELECT nome, cidade, capacidade, endereco
        FROM estadios
        ORDER BY capacidade DESC;
        """
    elif "times" in query_lower:
        return """
        SELECT nome, cidade, estado, data_fundacao, cores
        FROM times
        ORDER BY nome;
        """
    elif "socio" in query_lower or "sócio" in query_lower:
        return """
        SELECT t.nome AS torcedor, p.nome AS plano, p.valor_mensal,
               st.data_adesao, st.status
        FROM socio_torcedor st
        JOIN torcedores t ON st.torcedor_id = t.torcedor_id
        JOIN planos_socio p ON st.plano_id = p.plano_id
        ORDER BY p.valor_mensal DESC;
        """
    else:
        return """
        SELECT t.nome AS time, COUNT(j.jogo_id) AS total_jogos,
               SUM(CASE WHEN t.time_id = j.time_casa_id AND j.placar_casa > j.placar_visitante THEN 1
                        WHEN t.time_id = j.time_visitante_id AND j.placar_visitante > j.placar_casa THEN 1
                        ELSE 0 END) AS vitorias
        FROM times t
        LEFT JOIN jogos j ON t.time_id = j.time_casa_id OR t.time_id = j.time_visitante_id
        GROUP BY t.nome
        ORDER BY vitorias DESC
        LIMIT 10;
        """

# Função para executar SQL no banco de dados
def execute_database_query(sql, engine):
    try:
        with st.spinner("Executando consulta..."):
            df = pd.read_sql_query(sql, engine)
            st.success(f"Consulta retornou {len(df)} registros")
            return df
    except Exception as e:
        st.error(f"Erro ao executar SQL: {str(e)}")
        return None

# Função para executar consulta simulada (modo Demo)
def execute_demo_query(sql):
    if "torcedores" in sql.lower():
        return pd.DataFrame({
            'nome': ['João Silva', 'Maria Souza', 'Carlos Santos', 'Ana Oliveira', 'Pedro Costa'],
            'email': ['joao@email.com', 'maria@email.com', 'carlos@email.com', 'ana@email.com', 'pedro@email.com'],
            'cidade': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Porto Alegre', 'São Paulo'],
            'estado': ['SP', 'RJ', 'MG', 'RS', 'SP'],
            'data_nascimento': ['1985-03-10', '1990-07-15', '1978-12-05', '1995-05-20', '1982-09-30']
        })
    elif "jogos" in sql.lower():
        return pd.DataFrame({
            'jogo_id': [1, 2, 3, 4, 5],
            'time_casa': ['Flamengo', 'Cruzeiro', 'São Paulo', 'Fluminense', 'Internacional'],
            'time_visitante': ['Corinthians', 'Grêmio', 'Palmeiras', 'Atlético Mineiro', 'Santos'],
            'data_hora': ['2023-03-15 16:00:00', '2023-03-16 19:30:00', '2023-03-17 20:00:00', 
                          '2023-03-18 16:00:00', '2023-03-19 18:30:00'],
            'placar_casa': [2, 0, 3, 1, 2],
            'placar_visitante': [1, 0, 2, 2, 2],
            'publico_total': [60000, 40000, 55000, 45000, 42000],
            'estadio': ['Maracanã', 'Mineirão', 'Morumbi', 'Maracanã', 'Arena do Grêmio']
        })
    elif "ingressos" in sql.lower():
        return pd.DataFrame({
            'ingresso_id': [1, 2, 3, 4, 5],
            'torcedor': ['João Silva', 'Maria Souza', 'Carlos Santos', 'Ana Oliveira', 'Pedro Costa'],
            'time_casa': ['Flamengo', 'Flamengo', 'Flamengo', 'Flamengo', 'Flamengo'],
            'time_visitante': ['Corinthians', 'Corinthians', 'Fluminense', 'Fluminense', 'Palmeiras'],
            'data_jogo': ['2023-03-15 16:00:00', '2023-03-15 16:00:00', '2023-04-01 16:00:00', 
                         '2023-04-01 16:00:00', '2023-06-20 20:00:00'],
            'setor': ['Arquibancada Leste', 'Arquibancada Oeste', 'Arquibancada Norte',
                     'Camarotes', 'Arquibancada Oeste'],
            'preco': [80.00, 80.00, 64.00, 240.00, 80.00]
        })
    elif "estadios" in sql.lower():
        return pd.DataFrame({
            'nome': ['Maracanã', 'Arena Corinthians', 'Mineirão', 'Arena do Grêmio', 'Morumbi'],
            'cidade': ['Rio de Janeiro', 'São Paulo', 'Belo Horizonte', 'Porto Alegre', 'São Paulo'],
            'capacidade': [78000, 49000, 61000, 55000, 66000],
            'endereco': ['Av. Presidente Castelo Branco, Portão 3', 'Av. Miguel Ignácio Curi, 111',
                        'Av. Antônio Abrahão Caram, 1001', 'Av. Padre Leopoldo Brentano, 110', 
                        'Praça Roberto Gomes Pedrosa, 1']
        })
    elif "socio" in sql.lower():
        return pd.DataFrame({
            'torcedor': ['Maria Souza', 'João Silva', 'Bruno Ribeiro', 'Ana Oliveira', 'Gustavo Martins'],
            'plano': ['Ouro', 'Prata', 'Ouro', 'Bronze', 'Diamante'],
            'valor_mensal': [149.90, 89.90, 149.90, 49.90, 299.90],
            'data_adesao': ['2021-05-10', '2022-01-15', '2022-02-18', '2022-08-22', '2021-12-30'],
            'status': ['ativo', 'ativo', 'ativo', 'ativo', 'ativo']
        })
    else:
        return pd.DataFrame({
            'time': ['Flamengo', 'São Paulo', 'Corinthians', 'Palmeiras', 'Cruzeiro'],
            'total_jogos': [10, 8, 6, 7, 5],
            'vitorias': [7, 5, 4, 4, 3]
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
        
        # Configuração do banco de dados
        with st.expander("Conexão com o Banco", expanded=True):
            # Neon requer informações específicas
            st.info("Configure a conexão com seu banco Neon:")
            host = st.text_input("Host Neon", placeholder="ep-name-12345.region.neon.tech")
            port = st.text_input("Porta", value="5432")
            database = st.text_input("Database", value="neondb")
            username = st.text_input("Usuário", value="")
            password = st.text_input("Senha", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Conectar ao Banco"):
                    if host and port and database and username and password:
                        if connect_to_database(host, port, database, username, password):
                            st.session_state.is_connected = True
                            st.session_state.is_demo = False
                            st.success("Banco de dados conectado com sucesso!")
                    else:
                        st.error("Preencha todos os campos de conexão")
            
            with col2:
                if st.button("Modo Demo"):
                    st.session_state.is_demo = True
                    st.session_state.is_connected = False
                    st.success("Modo de demonstração ativado!")
        
        # Status da conexão
        if st.session_state.is_connected:
            st.success(f"✓ Conectado ao banco {database}")
        elif st.session_state.is_demo:
            st.info("ℹ️ Modo Demo ativo")
        
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
            placeholder="Ex: Mostrar todos os jogos recentes\nMostrar os torcedores cadastrados\nListar os ingressos vendidos",
            height=100
        )
        
        # Sugestões de perguntas
        with st.expander("📝 Sugestões de perguntas"):
            st.markdown("""
            - Mostrar todos os torcedores cadastrados
            - Listar os jogos mais recentes
            - Mostrar os ingressos vendidos
            - Quais são os estádios cadastrados?
            - Informações dos times
            - Mostrar planos de sócio torcedor
            """)
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Gerar SQL"):
                if query:
                    with st.spinner("Gerando SQL..."):
                        sql = generate_sql(query)
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
                    
                    if results is not None:
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
                        # Encontrar colunas adequadas para visualização
                        text_cols = df.select_dtypes(include=['object']).columns.tolist()
                        num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                        
                        if text_cols and num_cols:  # Se temos colunas de texto e numéricas
                            default_x = text_cols[0]
                            default_y = num_cols[0]
                            
                            # Opções para o gráfico
                            st.subheader("Configurações de visualização")
                            chart_type = st.selectbox("Tipo de gráfico", ["Barra", "Linha", "Pizza", "Dispersão"])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                x_axis = st.selectbox("Eixo X", df.columns.tolist(), 
                                                     index=df.columns.get_loc(default_x) if default_x in df.columns else 0)
                            with col2:
                                if num_cols:
                                    y_axis = st.selectbox("Eixo Y", num_cols, 
                                                         index=0)
                                else:
                                    y_axis = st.selectbox("Eixo Y", df.columns.tolist(),
                                                        index=min(1, len(df.columns)-1))
                            
                            # Criar gráfico
                            try:
                                if chart_type == "Barra":
                                    fig = px.bar(df, x=x_axis, y=y_axis, title=f"{y_axis} por {x_axis}")
                                    st.plotly_chart(fig, use_container_width=True)
                                elif chart_type == "Linha":
                                    fig = px.line(df, x=x_axis, y=y_axis, title=f"{y_axis} por {x_axis}")
                                    st.plotly_chart(fig, use_container_width=True)
                                elif chart_type == "Pizza":
                                    fig = px.pie(df, names=x_axis, values=y_axis, title=f"Distribuição de {y_axis}")
                                    st.plotly_chart(fig, use_container_width=True)
                                else:  # Dispersão
                                    fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
                                    st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Erro ao criar visualização: {str(e)}")
                        else:
                            st.warning("Não há colunas numéricas para visualização adequada.")
                    else:
                        st.warning("Os dados não têm colunas suficientes para visualização.")
                else:
                    st.info("Execute a consulta para visualizar os dados")
    else:
        st.info("👈 Conecte ao banco ou ative o Modo Demo para começar")
        
        st.header("📌 Como funciona")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1️⃣ Configuração\nConfigure a conexão com o banco de dados de futebol.")
        with col2:
            st.markdown("### 2️⃣ Pergunte\nFaça perguntas sobre torcedores, jogos, ingressos, etc.")
        with col3:
            st.markdown("### 3️⃣ Analise\nVisualize os resultados com gráficos interativos.")
    
    # Rodapé
    st.divider()
    st.markdown("DataTalk © 2025 - Consulta de banco de dados de futebol por linguagem natural")

# Iniciar o aplicativo
if __name__ == "__main__":
    main()
