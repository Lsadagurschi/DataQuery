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

# Arquivo de histórico de consultas
QUERY_HISTORY_FILE = os.path.join(LEARNING_DIR, "query_history.json")
NLP_MODEL_FILE = os.path.join(LEARNING_DIR, "nlp_model.json")

# Inicializar estados da sessão
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False
if 'is_demo' not in st.session_state:
    st.session_state.is_demo = False
if 'current_sql' not in st.session_state:
    st.session_state.current_sql = None
if 'current_natural_query' not in st.session_state:
    st.session_state.current_natural_query = None
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'db_engine' not in st.session_state:
    st.session_state.db_engine = None
if 'nlp_processor' not in st.session_state:
    st.session_state.nlp_processor = None

# Função para exibir o cabeçalho
def display_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.write("⚽")  # Emoji como logo
    with col2:
        st.title("DataTalk - Aprendizado Dinâmico")
        st.write("Consulta avançada com aprendizado contínuo")
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

# Função para conectar ao banco de dados
def connect_to_database(db_type, host, port, database, username, password):
    try:
        if db_type == "PostgreSQL":
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=require"
        else:  # MySQL
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        
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
        return False

# Processador de Linguagem Natural com Aprendizado
class NLPProcessor:
    def __init__(self, model_file=NLP_MODEL_FILE):
        self.model_file = model_file
        self.load_model()
        
    def load_model(self):
        """Carrega o modelo NLP do arquivo ou inicializa um novo"""
        try:
            if os.path.exists(self.model_file):
                with open(self.model_file, 'r', encoding='utf-8') as f:
                    model_data = json.load(f)
                    self.entities = model_data.get('entities', {})
                    self.operations = model_data.get('operations', {})
                    self.attributes = model_data.get('attributes', {})
                    self.specific_queries = model_data.get('specific_queries', {})
                    self.learned_queries = model_data.get('learned_queries', [])
            else:
                self._initialize_default_model()
        except Exception as e:
            st.warning(f"Erro ao carregar modelo NLP: {str(e)}. Inicializando modelo padrão.")
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Inicializa o modelo com valores padrão"""
        # Dicionário de entidades e atributos do modelo de dados
        self.entities = {
            'estadio': ['estadio', 'estadios', 'arena', 'arenas', 'estádio', 'estádios'],
            'time': ['time', 'times', 'clube', 'clubes', 'equipe', 'equipes'],
            'torcedor': ['torcedor', 'torcedores', 'fã', 'fãs', 'fan', 'fans'],
            'jogo': ['jogo', 'jogos', 'partida', 'partidas', 'confronto', 'confrontos', 'match', 'matches'],
            'ingresso': ['ingresso', 'ingressos', 'ticket', 'tickets', 'bilhete', 'bilhetes', 'entrada', 'entradas'],
            'socio': ['socio', 'socios', 'sócio', 'sócios', 'membro', 'membros', 'associado', 'associados']
        }
        
        # Dicionário de operações e palavras relacionadas
        self.operations = {
            'count': ['quantos', 'quantidade', 'total', 'número', 'numero', 'contar', 'conte', 'contagem'],
            'list': ['listar', 'liste', 'mostrar', 'mostre', 'exibir', 'exiba', 'quais', 'quais são', 'qual'],
            'filter': ['filtrar', 'filtre', 'onde', 'em que', 'apenas', 'somente', 'com', 'que tem', 'que tenha'],
            'order': ['ordenar', 'ordene', 'classificar', 'classifique', 'ordem', 'ranking'],
            'group': ['agrupar', 'agrupe', 'por', 'agrupado', 'grupo']
        }
        
        # Dicionário de atributos específicos
        self.attributes = {
            'nome': ['nome', 'nomes', 'chamado', 'chamados', 'denomina'],
            'cidade': ['cidade', 'cidades', 'local', 'locais', 'localidade', 'localidades'],
            'estado': ['estado', 'estados', 'uf', 'província', 'provincias'],
            'capacidade': ['capacidade', 'lotação', 'tamanho', 'dimensão', 'dimensões', 'pessoas'],
            'data': ['data', 'datas', 'dia', 'dias', 'quando'],
            'valor': ['valor', 'valores', 'preço', 'preços', 'custo', 'custos', 'quanto', 'quantia'],
            'status': ['status', 'situação', 'estado', 'condição', 'condições']
        }
        
        # Dicionário de consultas específicas pré-definidas
        self.specific_queries = {
            'contar_estadios': {
                'patterns': [
                    r'quantos est[áa]dios',
                    r'n[úu]mero de est[áa]dios',
                    r'total de est[áa]dios',
                    r'quantidade de est[áa]dios',
                    r'quantas arenas',
                    r'contar est[áa]dios'
                ],
                'sql': """
                SELECT COUNT(*) AS total_estadios
                FROM estadios;
                """
            },
            'listar_estadios': {
                'patterns': [
                    r'(?:listar|mostrar|exibir|quais)(?:.+?)est[áa]dios',
                    r'(?:lista|exibição)(?:.+?)est[áa]dios',
                    r'todos os est[áa]dios',
                    r'est[áa]dios(?:.+?)(?:cadastrados|registrados)',
                ],
                'sql': """
                SELECT nome, cidade, capacidade, endereco
                FROM estadios
                ORDER BY nome;
                """
            },
            # Outras consultas específicas...
        }
        
        # Lista de consultas aprendidas
        self.learned_queries = []
    
    def save_model(self):
        """Salva o modelo NLP atualizado no arquivo"""
        model_data = {
            'entities': self.entities,
            'operations': self.operations,
            'attributes': self.attributes,
            'specific_queries': self.specific_queries,
            'learned_queries': self.learned_queries
        }
        
        try:
            with open(self.model_file, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar modelo NLP: {str(e)}")
            return False
    
    def process_query(self, query: str) -> str:
        """
        Processa uma consulta em linguagem natural e retorna SQL
        
        Args:
            query: A pergunta em linguagem natural
            
        Returns:
            SQL gerado
        """
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
        
        # 3. Identificar entidades principais na consulta
        entity_type = self._identify_entity(query)
        
        # 4. Identificar operação
        operation = self._identify_operation(query)
        
        # 5. Gerar SQL com base na entidade e operação
        if entity_type == 'estadio':
            if operation == 'count':
                return """
                SELECT COUNT(*) AS total_estadios
                FROM estadios;
                """
            # Outras operações...
            
        # SQL padrão se não conseguir identificar
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
    
    def learn_query(self, natural_query: str, sql_query: str, was_successful: bool = True):
        """
        Adiciona uma nova consulta ao aprendizado
        
        Args:
            natural_query: A pergunta em linguagem natural
            sql_query: O SQL que responde à pergunta
            was_successful: Se a consulta foi bem-sucedida
        """
        if not was_successful:
            return
            
        natural_query = natural_query.lower().strip()
        
        # Verificar se já existe uma consulta semelhante
        for learned in self.learned_queries:
            if self._calculate_similarity(natural_query, learned['natural_query']) > 0.8:
                # Atualizar a consulta existente com a mais recente
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
        
        # Extrair e adicionar novos termos ao vocabulário
        self._extract_keywords(natural_query)
        
        # Salvar o modelo atualizado
        self.save_model()
    
    def _extract_keywords(self, query: str):
        """
        Extrai palavras-chave da consulta para expandir o vocabulário
        
        Args:
            query: A pergunta em linguagem natural
        """
        # Simplificação: dividir por espaços e filtrar palavras comuns
        common_words = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'e', 'que', 'para', 'por'}
        words = [word for word in query.split() if word not in common_words and len(word) > 3]
        
        # Adicionar palavras aos dicionários apropriados
        for word in words:
            # Verificar se a palavra já existe em algum dicionário
            exists = False
            for entity, terms in self.entities.items():
                if word in terms:
                    exists = True
                    break
            
            if not exists:
                # Tentar identificar a qual entidade a palavra pertence
                # (Simplificação: algoritmo baseado em sufixos comuns)
                if word.endswith('s'):
                    singular = word[:-1]
                    for entity, terms in self.entities.items():
                        if singular in terms:
                            self.entities[entity].append(word)
                            break
    
    def _identify_entity(self, query: str) -> str:
        """
        Identifica a entidade principal na consulta
        
        Args:
            query: A pergunta em linguagem natural
            
        Returns:
            Tipo de entidade
        """
        max_score = 0
        identified_entity = None
        
        for entity_type, keywords in self.entities.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > max_score:
                max_score = score
                identified_entity = entity_type
        
        return identified_entity or 'time'  # fallback para 'time'
    
    def _identify_operation(self, query: str) -> str:
        """
        Identifica a operação na consulta
        
        Args:
            query: A pergunta em linguagem natural
            
        Returns:
            Tipo de operação
        """
        max_score = 0
        identified_operation = None
        
        for operation_type, keywords in self.operations.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > max_score:
                max_score = score
                identified_operation = operation_type
        
        return identified_operation or 'list'  # fallback para 'list'
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """
        Calcula similaridade entre duas consultas (implementação simplificada)
        
        Args:
            query1: Primeira consulta
            query2: Segunda consulta
            
        Returns:
            Score de similaridade entre 0 e 1
        """
        # Normalizar e dividir em palavras
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        # Interseção de palavras
        common_words = words1.intersection(words2)
        
        # Coeficiente de Jaccard
        if len(words1.union(words2)) == 0:
            return 0
        return len(common_words) / len(words1.union(words2))

# Carregar histórico de consultas do arquivo
def load_query_history():
    try:
        if os.path.exists(QUERY_HISTORY_FILE):
            with open(QUERY_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.warning(f"Erro ao carregar histórico de consultas: {str(e)}")
        return []

# Salvar histórico de consultas no arquivo
def save_query_history(history):
    try:
        with open(QUERY_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.warning(f"Erro ao salvar histórico de consultas: {str(e)}")
        return False

# Função para gerar SQL com processador NLP
def generate_sql(query, nlp_processor):
    return nlp_processor.process_query(query)

# Função para executar SQL no banco de dados
def execute_database_query(sql, engine):
    try:
        with st.spinner("Executando consulta..."):
            df = pd.read_sql_query(sql, engine)
            st.success(f"Consulta retornou {len(df)} registros")
            return df, True
    except Exception as e:
        st.error(f"Erro ao executar SQL: {str(e)}")
        return None, False

# Função para executar consulta simulada (modo Demo)
def execute_demo_query(sql):
    # Implementação com dados de exemplo (como no código anterior)
    if "COUNT(*)" in sql and "estadios" in sql:
        return pd.DataFrame({'total_estadios': [5]}), True
    
    # Adicionar outras verificações para diferentes consultas
    
    # Fallback
    return pd.DataFrame({
        'time': ['Flamengo', 'São Paulo', 'Corinthians', 'Palmeiras', 'Cruzeiro'],
        'total_jogos': [10, 8, 6, 7, 5],
        'vitorias': [7, 5, 4, 4, 3]
    }), True

# Função principal
def main():
    # Inicializar o processador NLP se ainda não estiver inicializado
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
        
        # Configuração do banco de dados
        with st.expander("Conexão com o Banco", expanded=True):
            db_type = st.selectbox(
                "Tipo de Banco de Dados",
                ["PostgreSQL", "MySQL"],
                index=0
            )
            
            host = st.text_input("Host", placeholder="hostname ou endpoint")
            port = st.text_input("Porta", value="3306" if db_type == "MySQL" else "5432")
            database = st.text_input("Nome do Banco", value="neondb")
            username = st.text_input("Usuário", value="")
            password = st.text_input("Senha", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Conectar ao Banco"):
                    if host and port and database and username and password:
                        if connect_to_database(db_type, host, port, database, username, password):
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
                with st.expander(f"Consulta {i+1}: {item['natural_query'][:30]}..."):
                    st.code(item['sql_query'], language="sql")
                    if st.button(f"Reutilizar #{i+1}", key=f"reuse_{i}"):
                        st.session_state.current_natural_query = item['natural_query']
                        st.session_state.current_sql = item['sql_query']
                        st.rerun()
        
        # Estatísticas de aprendizado
        with st.expander("📊 Estatísticas de Aprendizado"):
            st.write(f"Consultas aprendidas: {len(st.session_state.nlp_processor.learned_queries)}")
            
            # Top consultas mais usadas
            if st.session_state.nlp_processor.learned_queries:
                top_queries = sorted(
                    st.session_state.nlp_processor.learned_queries, 
                    key=lambda x: x['used_count'], 
                    reverse=True
                )[:3]
                
                st.subheader("Top Consultas Aprendidas")
                for i, query in enumerate(top_queries):
                    st.write(f"{i+1}. \"{query['natural_query']}\" (Usada {query['used_count']}x)")
            
            if st.button("Limpar Modelo de Aprendizado"):
                st.session_state.nlp_processor._initialize_default_model()
                st.session_state.nlp_processor.save_model()
                st.success("Modelo de aprendizado reiniciado!")
        
        # Botão de logout
        if st.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Área principal
    if st.session_state.is_connected or st.session_state.is_demo:
        st.header("💬 Faça sua pergunta")
        
        # Input para a pergunta em linguagem natural
        natural_query = st.text_area(
            "O que você gostaria de saber?",
            value=st.session_state.current_natural_query if st.session_state.current_natural_query else "",
            placeholder="Ex: Quantos estádios estão cadastrados?",
            height=100
        )
        
        # Sugestões de perguntas
        with st.expander("📝 Sugestões de perguntas"):
            st.markdown("""
            - Quantos estádios estão cadastrados?
            - Listar todos os estádios
            - Quais são os estádios com maior capacidade?
            - Mostrar todos os jogos recentes
            - Listar os ingressos vendidos
            - Quantos torcedores são sócios?
            """)
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Gerar SQL"):
                if natural_query:
                    with st.spinner("Gerando SQL..."):
                        sql = generate_sql(natural_query, st.session_state.nlp_processor)
                        st.session_state.current_natural_query = natural_query
                        st.session_state.current_sql = sql
                        st.success("SQL gerado com sucesso!")
        
        with col2:
            if st.button("Executar") and st.session_state.current_sql:
                with st.spinner("Executando consulta..."):
                    if st.session_state.is_demo:
                        results, success = execute_demo_query(st.session_state.current_sql)
                    else:
                        results, success = execute_database_query(st.session_state.current_sql, st.session_state.db_engine)
                    
                    if success and results is not None:
                        st.session_state.current_results = results
                        
                        # Adicionar ao histórico
                        history_item = {
                            "timestamp": datetime.now().isoformat(),
                            "natural_query": st.session_state.current_natural_query,
                            "sql_query": st.session_state.current_sql,
                            "success": success
                        }
                        
                        if history_item not in st.session_state.query_history:
                            st.session_state.query_history.append(history_item)
                            
                            # Salvar no histórico
                            save_query_history(st.session_state.query_history)
                            
                            # Adicionar ao aprendizado
                            st.session_state.nlp_processor.learn_query(
                                st.session_state.current_natural_query,
                                st.session_state.current_sql,
                                success
                            )
                        
                        st.success("Consulta executada com sucesso!")
        
        # Exibir resultados se disponíveis
        if st.session_state.current_sql:
            tabs = st.tabs(["📊 Resultados", "📝 SQL", "📈 Visualização", "🔄 Feedback"])
            
            with tabs[0]:
                if "current_results" in st.session_state and st.session_state.current_results is not None:
                    st.dataframe(st.session_state.current_results, use_container_width=True)
                else:
                    st.info("Execute a consulta para ver resultados")
            
            with tabs[1]:
                st.code(st.session_state.current_sql, language="sql")
                
                # Opção para editar SQL manualmente
                edited_sql = st.text_area(
                    "Editar SQL manualmente:", 
                    value=st.session_state.current_sql,
                    height=150
                )
                
                if st.button("Usar SQL Editado"):
                    st.session_state.current_sql = edited_sql
                    st.success("SQL atualizado!")
            
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
                                    fig = px.line(df, x=x_
