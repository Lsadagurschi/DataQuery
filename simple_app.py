# Arquivo simples para verificar se o Streamlit Cloud está funcionando corretamente
import streamlit as st

st.title("DataTalk - Versão Básica")
st.write("Esta é uma versão simplificada do DataTalk para testar a implantação no Streamlit Cloud.")

if st.button("Clique para Testar"):
    st.success("O Streamlit Cloud está funcionando corretamente!")
    
st.write("Uma vez que este aplicativo estiver funcionando, podemos adicionar mais funcionalidades gradualmente.")
