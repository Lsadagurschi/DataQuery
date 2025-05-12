import streamlit as st
import pandas as pd
import json
import os
import re
import sqlparse
import openai
import time
from datetime import datetime

# Constantes para gerenciar o aprendizado
GOLD_LIST_FILE = "gold_list.json"
FEEDBACK_FILE = "feedback_log.json"

def _get_gold_list():
    """Carrega a lista de consultas exemplares"""
    if not os.path.exists(GOLD_LIST_FILE):
        return []
    
    try:
        with open(GOLD_LIST_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def _save_gold_list(gold_list):
    """Salva a lista de consultas exemplares"""
    with open(GOLD_LIST_FILE, 'w') as f:
        json.dump(gold_list, f, indent=2)

def _log_feedback(query, sql, feedback, details=None):
    """Registra feedback sobre consultas"""
    feedback_data = []
    
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r') as f:
                feedback_data = json.load(f)
        except:
            feedback_data = []
    
    feedback_data.append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "sql": sql,
        "feedback": feedback,
        "details": details
    })
    
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_data, f, indent=2)

def natural_to_sql(query, db_info):
    """Converte uma consulta em linguagem natural para SQL usando um modelo de NLP"""
    
    # Obter informações do schema do banco de dados
    from database import get_schema_info
    schema = get_schema_info(db_info)
    
    # Se não conseguiu obter o schema, use um exemplo
    if not schema:
        schema = {
            "tables": [
                {
                    "name": "vendas",
                    "columns": [
                        {"name": "id", "type": "integer"},
                        {"name": "data", "type": "date"},
                        {"name": "produto_id", "type": "integer"},
                        {"name": "cliente_id", "type": "integer"},
                        {"name": "valor", "type": "numeric"},
                        {"name": "quantidade", "type": "integer"}
                    ]
                },
                {
                    "name": "produtos",
                    "columns": [
                        {"name": "id", "type": "integer"},
                        {"name": "nome", "type": "varchar"},
                        {"name": "categoria", "type": "varchar"},
                        {"name": "preco", "type": "numeric"}
                    ]
                },
                {
                    "name": "clientes",
                    "columns": [
                        {"name": "id", "type": "integer"},
                        {"name": "nome", "type": "varchar"},
                        {"name": "email", "type": "varchar"},
                        {"name": "regiao", "type": "varchar"}
                    ]
                }
            ],
            "relationships": [
                {"table": "vendas", "column": "produto_id", "foreign_table": "produtos", "foreign_column": "id"},
                {"table": "vendas", "column": "cliente_id", "foreign_table": "clientes", "foreign_column": "id"}
            ]
        }
    
    # Exemplos de consultas bem-sucedidas (Gold List)
    gold_examples = _get_gold_list()
    examples_text = ""
    
    if gold_examples:
        examples_text = "Exemplos de consultas bem-sucedidas:\n\n"
        
        for example in gold_examples[:3]:  # Use apenas os 3 primeiros exemplos
            examples_text += f"Query: {example['query']}\nSQL: {example['sql']}\n\n"
    
    # Criar o prompt para o modelo
    prompt = f"""
    Você é um especialista em converter perguntas em linguagem natural para SQL.
    
    Schema do banco de dados:
    {json.dumps(schema, indent=2)}
    
    {examples_text}
    
    Pergunta do usuário: {query}
    
    Gere apenas o código SQL que responde à pergunta. Não inclua explicações.
    """
    
    try:
        # Verificar se há chave API nos secrets do Streamlit
        api_key = None
        
        try:
            # Tenta acessar a chave da API nos secrets do Streamlit
            if "openai" in st.secrets and "api_key" in st.secrets["openai"]:
                api_key = st.secrets["openai"]["api_key"]
            elif "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except:
            # Se não conseguir acessar os secrets
            pass
            
        # Se não encontrou a chave no secrets, tenta uma versão simulada
        if not api_key:
            # Modo de simulação - retorna SQL de exemplo baseado em palavras-chave
            st.warning("Chave API OpenAI não encontrada. Usando modo de simulação.")
            
            # Exemplos de consultas simuladas
            keywords_mapping = {
                "venda": "SELECT v.data, p.nome, SUM(v.valor) as total_vendas\nFROM vendas v\nJOIN produtos p ON v.produto_id = p.id\nGROUP BY v.data, p.nome\nORDER BY v.data DESC;",
                "produto": "SELECT p.nome, p.categoria, p.preco, SUM(v.quantidade) as total_vendido\nFROM produtos p\nLEFT JOIN vendas v ON p.id = v.produto_id\nGROUP BY p.nome, p.categoria, p.preco\nORDER BY total_vendido DESC;",
                "cliente": "SELECT c.nome, c.regiao, COUNT(v.id) as num_compras, SUM(v.valor) as total_gasto\nFROM clientes c\nLEFT JOIN vendas v ON c.id = v.cliente_id\nGROUP BY c.nome, c.regiao\nORDER BY total_gasto DESC;",
                "região": "SELECT c.regiao, COUNT(DISTINCT c.id) as num_clientes, SUM(v.valor) as total_vendas\nFROM clientes c\nLEFT JOIN vendas v ON c.id = v.cliente_id\nGROUP BY c.regiao\nORDER BY total_vendas DESC;",
                "mês": "SELECT EXTRACT(MONTH FROM v.data) as mes, EXTRACT(YEAR FROM v.data) as ano, SUM(v.valor) as total_vendas\nFROM vendas v\nGROUP BY mes, ano\nORDER BY ano DESC, mes DESC;"
            }
            
            # Busca por palavras-chave na consulta
            for keyword, sql in keywords_mapping.items():
                if keyword.lower() in query.lower():
                    return sql
            
            # Resposta padrão se nenhuma palavra-chave for encontrada
            return "SELECT * FROM vendas ORDER BY data DESC LIMIT 10;"
            
        # Modo real com API OpenAI
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em gerar SQL preciso."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2  # Para resultados mais determinísticos
        )
        
        # A forma de acessar o conteúdo da resposta mudou na nova API
        sql = response.choices[0].message.content.strip()
        
        # Limpar e formatar o SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()
        sql = sqlparse.format(sql, reindent=True, keyword_case='upper')
        
        return sql
    
    except Exception as e:
        st.error(f"Erro ao gerar SQL: {str(e)}")
        # Modo de fallback para quando ocorrer um erro
        st.warning("Usando SQL de exemplo devido a um erro na geração.")
        return "SELECT v.data, p.nome, SUM(v.valor) as total_vendas\nFROM vendas v\nJOIN produtos p ON v.produto_id = p.id\nGROUP BY v.data, p.nome\nORDER BY v.data DESC LIMIT 10;"

def validate_query(sql, db_info):
    """Verifica se a consulta SQL é segura e válida"""
    
    # Verificar se é uma consulta de leitura (e não modificação)
    sql_lower = sql.lower()
    
    if re.search(r'\b(insert|update|delete|drop|alter|create|truncate)\b', sql_lower):
        return False, "Consultas de modificação não são permitidas"
    
    # Verificar sintaxe SQL (isso é muito simplificado)
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False, "Consulta SQL inválida"
    except:
        return False, "Erro ao analisar a consulta SQL"
    
    # Em uma implementação real, você faria validações mais rigorosas,
    # como verificar se as tabelas e colunas existem no banco
    
    return True, "Consulta validada com sucesso"

def improve_model(query, sql, feedback, details=None):
    """Melhora o modelo com base no feedback"""
    
    # Registrar feedback
    _log_feedback(query, sql, feedback, details)
    
    # Se for feedback positivo, considerar adicionar à Gold List
    if feedback == "positive" and query and sql:
        gold_list = _get_gold_list()
        
        # Verificar se consulta similar já existe na Gold List
        existing = False
        for item in gold_list:
            if query.lower() == item["query"].lower():
                existing = True
                break
        
        if not existing:
            gold_list.append({
                "query": query,
                "sql": sql,
                "added_at": datetime.now().isoformat()
            })
            
            # Limitar a lista a 100 exemplos
            if len(gold_list) > 100:
                gold_list = gold_list[-100:]
            
            _save_gold_list(gold_list)
    
    # Em uma implementação real, você poderia treinar incrementalmente o modelo
    # ou ajustar os prompts com base no feedback acumulado
