import streamlit as st

st.title("DataTalk - Teste de Conectividade")
st.write("Se você está vendo esta mensagem, a conexão está funcionando!")
st.write("Clique no botão abaixo para confirmar:")
if st.button("Confirmar"):
    st.success("Conexão estabelecida com sucesso!")
