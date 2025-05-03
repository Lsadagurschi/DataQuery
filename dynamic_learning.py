import streamlit as st
import pandas as pd
import time
import os
import json
import re
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="DataTalk - Aprendizado Dinâmico", 
    page_icon="⚽", 
    layout="wide"
)

# Diretório para armazenar dados de aprendizado
LEARNING_DIR = "learning_data"
os.makedirs(LEARNING_DIR, exist_ok=True)
QUERY_HISTORY_FILE = os.path.join(LEARNING_DIR, "query_history.json")
NLP_MODEL_FILE = os.path.join(LEARNING_DIR, "nlp_model.json")

# Inicializar estados da sessão
for key in ['authenticated', 'is_connected', 'is_demo', 'current_sql', 
            'current_natural_query', 'current_results', 'db_engine', 'nlp_processor']:
    if key not in st.session_state:
        st.session_state[key] = None if key in ['current_sql', 'current_natural_query', 
                                              'current_results', 'db_engine', 'nlp_processor'] else False
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Classe para processamento de linguagem natural com aprendizado
class NLPProcessor:
    def __init__(self):
        self.model_file = NLP_MODEL_FILE
        self.load_model()
    
    def load_model(self):
        """Carrega o modelo NLP do arquivo ou inicializa um novo"""
        try:
            if os.path.exists(self.model_file):
                with open(self.model_file, 'r', encoding='utf-8') as f:
                    model_data = json.load(f)
                    self.entities = model_data.get('entities', {})
                    self.operations = model_data.get('operations', {})
                    self.specific_queries = model_data.get('specific_queries', {})
                    self.learned_queries = model_data.get('learned_queries', [])
            else:
                self._initialize_default_model()
        except Exception as e:
            st.warning(f"Erro ao carregar modelo NLP. Inicializando modelo padrão.")
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Inicializa o modelo com valores padrão"""
        # Dicionário de entidades
        self.entities = {
            'estadio': ['estadio', 'estadios', 'arena', 'arenas', 'estádio', 'estádios'],
            'time': ['time', 'times', 'clube', 'clubes', 'equipe', 'equipes'],
            'torcedor': ['torcedor', 'torcedores', 'fã', 'fãs', 'fan', 'fans'],
            'jogo': ['jogo', 'jogos', 'partida', 'partidas', 'confronto', 'confrontos'],
            'ingresso': ['ingresso', 'ingressos', 'ticket', 'tickets', 'bilhete', 'bilhetes'],
            'socio': ['socio', 'socios', 'sócio', 'sócios', 'membro', 'membros', 'associado']
        }
        
        # Dicionário de operações
        self.operations = {
            'count': ['quantos', 'quantidade', 'total', 'número', 'numero', 'contar'],
            'list': ['listar', 'liste', 'mostrar', 'mostre', 'exibir', 'exiba', 'quais'],
            'filter': ['filtrar', 'filtre', 'onde', 'apenas', 'somente', 'com'],
            'order': ['ordenar', 'ordene', 'classificar', 'classifique', 'ordem', 'ranking'],
            'group': ['agrupar', 'agrupe', 'por', 'agrupado', 'grupo']
        }
        
        # Consultas específicas predefinidas
        self.specific_queries = {
            'contar_estadios': {
                'patterns': [r'quantos est[áa]dios', r'total de est[áa]dios', r'quantas arenas'],
                'sql': "SELECT COUNT(*) AS total_estadios FROM estadios;"
            },
            'listar_estadios': {
                'patterns': [r'(?:listar|mostrar|exibir|quais)(?:.+?)est[áa]dios'],
                'sql': "SELECT nome, cidade, capacidade, endereco FROM estadios ORDER BY nome;"
            }
        }
        
        # Lista de consultas aprendidas
        self.learned_queries = []
    
    def save_model(self):
        """Salva o modelo NLP atualizado no arquivo"""
        model_data = {
            'entities': self.entities,
            'operations': self.operations,
            'specific_queries': self.specific_queries,
            'learned_queries': self.learned_queries
        }
        
        try:
            os.makedirs(os.path.dirname(self.model_file), exist_ok=True)
            with open(self.model_file, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar modelo NLP: {str(e)}")
            return False
    
    def process_query(self, query: str) -> str:
        """Processa uma consulta em linguagem natural e retorna SQL"""
        query = query.lower().strip()
        
        # 1. Verificar nas consultas aprendidas
        for learned in self.learned_queries:
            similarity = self._calculate_similarity(query, learned['natural_query'])
            if similarity > 0.7:  # Limiar de similaridade
                return learned['sql_query']
        
        # 2. Verificar consultas específicas pré-definidas
        for query_type, query_info in self.specific_queries.items():
            for pattern in query_info['patterns']:
                if re.search(pattern, query):
                    return query_info['sql']
        
        # 3. Identificar entidades e operações
        entity_type = self._identify_entity(query)
        operation = self._identify_operation(query)
        
        # 4. Gerar SQL com base na entidade e operação
        if entity_type == 'estadio':
            if operation == 'count':
                return "SELECT COUNT(*) AS total_estadios FROM estadios;"
            else:
                return "SELECT nome, cidade, capacidade, endereco FROM estadios ORDER BY nome;"
        elif entity_type == 'time':
            if operation == 'count':
                return "SELECT COUNT(*) AS total_times FROM times;"
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
        
        # Fallback para consulta padrão
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
    
    def learn_query(self, natural_query: str, sql_query: str, success: bool = True):
        """Adiciona uma nova consulta ao aprendizado"""
        if not success:
            return
            
        natural_query = natural_query.lower().strip()
        
        # Verificar se já existe uma consulta semelhante
        for learned in self.learned_queries:
            if self._calculate_similarity(natural_query, learned['natural_query']) > 0.8:
                learned['sql_query'] = sql_query
                learned['used_count'] += 1
                learned['last_used'] = datetime.now().isoformat()
                self.save_model()
                return
        
        # Adicionar nova consulta
        self.learned_queries.append({
            'natural_query': natural_query,
            'sql_query': sql_query,
            'created': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'used_count': 1
        })
        
        # Extrair e adicionar novos termos
        self._extract_new_terms(natural_query)
        self.save_model()
    
    def _extract_new_terms(self, query: str):
        """Extrai novos termos da consulta para enriquecer o modelo"""
        words = query.split()
        # Lógica simplificada de extração de termos
        for word in words:
            if len(word) < 4 or word in ['para', 'como', 'onde', 'quem']:
                continue
            
            # Verificar se já existe
            for category in self.entities.values():
                if word in category:
                    break
            else:
                # Adicionar à categoria mais provável com base em heurísticas simples
                if 'estádio' in query or 'arena' in query:
                    if word not in self.entities['estadio']:
                        self.entities['estadio'].append(word)
                elif 'time' in query or 'clube' in query:
                    if word not in self.entities['time']:
                        self.entities['time'].append(word)
    
    def _identify_entity(self, query: str) -> str:
        """Identifica a entidade principal na consulta"""
        max_score = 0
        identified_entity = None
        
        for entity_type, keywords in self.entities.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > max_score:
                max_score = score
                identified_entity = entity_type
        
        return identified_entity or 'time'  # fallback para 'time'
    
    def _identify_operation(self, query: str) -> str:
        """Identifica a operação na consulta"""
        max_score = 0
        identified_operation = None
        
        for operation_type, keywords in self.operations.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > max_score:
                max_score = score
                identified_operation = operation_type
        
        return identified_operation or 'list'  # fallback para 'list'
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calcula similaridade entre duas consultas"""
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        common_words = words1.intersection(words2)
        return len(common_words) / len(words1.union(words2)) if words1.union(words2) else 0

# Funções do aplicativo
def display_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("⚽")
    with col2:
        st.title("DataTalk - Aprendizado Dinâmico")
        st.write("Consulta avançada com aprendizado contínuo")
    st.divider()

def show_login_page():
    st.title("DataTalk - Login")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit and username == "admin" and password == "admin":
            st.session_state.authenticated = True
            st.session_state.user = {"username": username}
            st.success("Login realizado com sucesso!")
            st.rerun()
        elif submit:
            st.error("Usuário ou senha inválidos")

def connect_to_database(db_type, host, port, database, username, password):
    try:
        if db_type == "PostgreSQL":
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=require"
        else:  # MySQL
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        
        st.info(f"Conectando a {db_type}...")
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        st.session_state.db_engine = engine
        return True
    except Exception as e:
        st.error(f"Erro na conexão: {str(e)}")
        return False

def load_query_history():
    try:
        if os.path.exists(QUERY_HISTORY_FILE):
            with open(QUERY_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except:
        return []

def save_query_history(history):
    try:
        os.makedirs(os.path.dirname(QUERY_HISTORY_FILE), exist_ok=True)
        with open(QUERY_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def execute_database_query(sql, engine):
    try:
        df = pd.read_sql_query(sql, engine)
        return df, True
    except Exception as e:
        st.error(f"Erro ao executar SQL: {str(e)}")
        return None, False

def execute_demo_query(sql):
    # Dados de exemplo para modo demonstração
    if "COUNT(*)" in sql and "estadios" in sql:
        return pd.DataFrame({'total_estadios': [5]}), True
    elif "estadios" in sql:
        return pd.DataFrame({
            'nome': ['Maracanã', 'Arena Corinthians', 'Mineirão', 'Arena do Grêmio', 'Morumbi'],
            'cidade': ['Rio de Janeiro', 'São Paulo', 'Belo Horizonte', 'Porto Alegre', 'São Paulo'],
            'capacidade': [78000, 49000, 61000, 55000, 66000],
            'endereco': ['Av. Presidente Castelo Branco', 'Av. Miguel Ignácio Curi', 
                        'Av. Antônio Abrahão Caram', 'Av. Padre Leopoldo Brentano', 
                        'Praça Roberto Gomes Pedrosa']
        }), True
    else:
        return pd.DataFrame({
            'time': ['Flamengo', 'São Paulo', 'Corinthians', 'Palmeiras', 'Cruzeiro'],
            'total_jogos': [10, 8, 6, 7, 5],
            'vitorias': [7, 5, 4, 4, 3]
        }), True

# Função principal
def main():
    # Inicializar o processador NLP
    if st.session_state.nlp_processor is None:
        st.session_state.nlp_processor = NLPProcessor()
        
    # Carregar histórico de consultas
    if not st.session_state.query_history:
        st.session_state.query_history = load_query_history()
    
    # Verificar autenticação
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Exibir cabeçalho
    display_header()
    
    # Barra lateral
    with st.sidebar:
        st.header("🔗 Configuração")
        
        # Conexão com banco de dados
        with st.expander("Conexão com o Banco", expanded=True):
            db_type = st.selectbox("Tipo de Banco", ["PostgreSQL", "MySQL"], index=0)
            host = st.text_input("Host", value="localhost")
            port = st.text_input("Porta", value="3306" if db_type == "MySQL" else "5432")
            database = st.text_input("Nome do Banco", value="neondb")
            username = st.text_input("Usuário", value="")
            password = st.text_input("Senha", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Conectar"):
                    if connect_to_database(db_type, host, port, database, username, password):
                        st.session_state.is_connected = True
                        st.session_state.is_demo = False
                        st.success("Conectado!")
            with col2:
                if st.button("Modo Demo"):
                    st.session_state.is_demo = True
                    st.session_state.is_connected = False
                    st.success("Demo Ativo!")
        
        # Histórico de consultas
        if st.session_state.query_history:
            st.header("📜 Histórico")
            for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
                with st.expander(f"Consulta {i+1}"):
                    st.text(item.get('natural_query', '')[:30])
                    st.code(item.get('sql_query', ''), language="sql")
                    if st.button(f"Reutilizar #{i+1}", key=f"reuse_{i}"):
                        st.session_state.current_natural_query = item.get('natural_query', '')
                        st.session_state.current_sql = item.get('sql_query', '')
                        st.rerun()
        
        # Estatísticas de aprendizado
        with st.expander("📊 Aprendizado"):
            st.write(f"Consultas aprendidas: {len(st.session_state.nlp_processor.learned_queries)}")
            
            if st.button("Reiniciar Modelo"):
                st.session_state.nlp_processor._initialize_default_model()
                st.session_state.nlp_processor.save_model()
                st.success("Modelo reiniciado!")
        
        # Logout
        if st.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Área principal
    if st.session_state.is_connected or st.session_state.is_demo:
        st.header("💬 Faça sua pergunta")
        
        # Input para consulta
        natural_query = st.text_area(
            "O que você gostaria de saber?",
            value=st.session_state.current_natural_query or "",
            placeholder="Ex: Quantos estádios estão cadastrados?",
            height=100
        )
        
        # Sugestões de perguntas
        with st.expander("📝 Sugestões de perguntas"):
            st.markdown("""
            - Quantos estádios estão cadastrados?
            - Listar todos os estádios
            - Quais são os estádios com maior capacidade?
            """)
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Gerar SQL"):
                if natural_query:
                    sql = st.session_state.nlp_processor.process_query(natural_query)
                    st.session_state.current_natural_query = natural_query
                    st.session_state.current_sql = sql
                    st.success("SQL gerado com sucesso!")
        
        with col2:
            if st.button("Executar") and st.session_state.current_sql:
                if st.session_state.is_demo:
                    results, success = execute_demo_query(st.session_state.current_sql)
                else:
                    results, success = execute_database_query(
                        st.session_state.current_sql, 
                        st.session_state.db_engine
                    )
                
                if success and results is not None:
                    st.session_state.current_results = results
                    
                    # Adicionar ao histórico e aprendizado
                    history_item = {
                        "timestamp": datetime.now().isoformat(),
                        "natural_query": st.session_state.current_natural_query,
                        "sql_query": st.session_state.current_sql
                    }
                    
                    # Evitar duplicados
                    if not any(item.get('sql_query') == st.session_state.current_sql 
                              for item in st.session_state.query_history):
                        st.session_state.query_history.append(history_item)
                        save_query_history(st.session_state.query_history)
                        
                        # Adicionar ao aprendizado
                        st.session_state.nlp_processor.learn_query(
                            st.session_state.current_natural_query,
                            st.session_state.current_sql,
                            success
                        )
                    
                    st.success("Consulta executada com sucesso!")
        
        # Exibir resultados
        if st.session_state.current_sql:
            tabs = st.tabs(["📊 Resultados", "📝 SQL", "📈 Visualização", "🔄 Feedback"])
            
            with tabs[0]:  # Resultados
                if "current_results" in st.session_state and st.session_state.current_results is not None:
                    st.dataframe(st.session_state.current_results, use_container_width=True)
                else:
                    st.info("Execute a consulta para ver resultados")
            
            with tabs[1]:  # SQL
                st.code(st.session_state.current_sql, language="sql")
                
                # Edição manual do SQL
                edited_sql = st.text_area("Editar SQL:", value=st.session_state.current_sql, height=150)
                if edited_sql != st.session_state.current_sql:
                    if st.button("Usar SQL Editado"):
                        st.session_state.current_sql = edited_sql
                        st.success("SQL atualizado!")
                        
                        # Aprender com a correção manual
                        st.session_state.nlp_processor.learn_query(
                            st.session_state.current_natural_query,
                            edited_sql,
                            True
                        )
            
            with tabs[2]:  # Visualização
                if "current_results" in st.session_state and st.session_state.current_results is not None:
                    df = st.session_state.current_results
                    if len(df.columns) >= 2:
                        chart_type = st.selectbox("Tipo de gráfico", 
                                                ["Barra", "Linha", "Pizza", "Dispersão"])
                        
                        # Identificar colunas numéricas/categóricas
                        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            x_col = st.selectbox("Eixo X", df.columns.tolist(), index=0)
                        with col2:
                            if numeric_cols:
                                y_col = st.selectbox("Eixo Y", numeric_cols, index=0)
                            else:
                                y_col = st.selectbox("Eixo Y", df.columns.tolist(), 
                                                   index=min(1, len(df.columns)-1))
                        
                        try:
                            if chart_type == "Barra":
                                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} por {x_col}")
                            elif chart_type == "Linha":
                                fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} por {x_col}")
                            elif chart_type == "Pizza":
                                fig = px.pie(df, names=x_col, values=y_col)
                            else:
                                fig = px.scatter(df, x=x_col, y=y_col)
                            
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Erro ao criar gráfico: {str(e)}")
                    else:
                        st.info("Dados insuficientes para visualização")
            
            with tabs[3]:  # Feedback
                st.subheader("Feedback de Aprendizagem")
                st.write("Você achou que a consulta SQL gerada foi adequada para sua pergunta?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Sim, foi correta"):
                        st.session_state.nlp_processor.learn_query(
                            st.session_state.current_natural_query,
                            st.session_state.current_sql,
                            True
                        )
                        st.success("Obrigado pelo feedback! O sistema aprendeu com esta consulta.")
                
                with col2:
                    if st.button("👎 Não, precisou ajustes"):
                        st.write("Por favor, edite o SQL na aba 'SQL' para ajudar o sistema a aprender.")
    else:
        st.info("👈 Conecte ao banco ou ative o Modo Demo para começar")

# Iniciar o aplicativo
if __name__ == "__main__":
    main()
