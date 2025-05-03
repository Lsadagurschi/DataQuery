import streamlit as st
import sys
import os
import traceback

# Configuração básica
st.set_page_config(
    page_title="DataTalk Debug",
    page_icon="🔍",
)

try:
    # Cabeçalho
    st.title("DataTalk - Modo Debug")
    st.write("Versão de diagnóstico para identificar problemas")
    
    # Informações do sistema
    st.subheader("Informações do Sistema")
    st.code(f"Python: {sys.version}")
    st.code(f"Streamlit: {st.__version__}")
    st.code(f"Diretório atual: {os.getcwd()}")
    
    # Teste de interatividade
    st.subheader("Teste de Interatividade")
    if "counter" not in st.session_state:
        st.session_state.counter = 0
    
    if st.button("Incrementar Contador"):
        st.session_state.counter += 1
    
    st.write(f"Valor do contador: {st.session_state.counter}")

    # Estrutura de diretórios
    st.subheader("Estrutura de arquivos")
    !find . -type f -name "*.py" | sort
    
    st.success("Aplicação Debug executada com sucesso!")
    
except Exception as e:
    st.error(f"Erro na execução: {str(e)}")
    st.code(traceback.format_exc())
