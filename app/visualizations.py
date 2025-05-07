import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import json

def create_visualization(df, x_column, y_column, chart_type):
    """Cria uma visualização com base nos dados e tipo de gráfico"""
    
    if df.empty:
        return None
    
    # Verificar se as colunas existem
    if x_column not in df.columns or y_column not in df.columns:
        st.error("Colunas selecionadas não existem nos dados.")
        return None
    
    # Criar visualização com Plotly
    if chart_type == "Barras":
        fig = px.bar(df, x=x_column, y=y_column, title=f"{y_column} por {x_column}")
    elif chart_type == "Linhas":
        fig = px.line(df, x=x_column, y=y_column, title=f"{y_column} por {x_column}")
    elif chart_type == "Dispersão":
        fig = px.scatter(df, x=x_column, y=y_column, title=f"{y_column} por {x_column}")
    elif chart_type == "Pizza":
        fig = px.pie(df, names=x_column, values=y_column, title=f"{y_column} por {x_column}")
    elif chart_type == "Área":
        fig = px.area(df, x=x_column, y=y_column, title=f"{y_column} por {x_column}")
    elif chart_type == "Histograma":
        fig = px.histogram(df, x=x_column, title=f"Distribuição de {x_column}")
    elif chart_type == "BoxPlot":
        fig = px.box(df, x=x_column, y=y_column, title=f"Distribuição de {y_column} por {x_column}")
    else:
        st.error("Tipo de gráfico não suportado.")
        return None
    
    # Ajustar layout
    fig.update_layout(
        autosize=True,
        height=500,
        margin=dict(l=50, r=50, b=100, t=100, pad=4),
        paper_bgcolor="white",
    )
    
    return fig

def export_visualization(fig, filename):
    """Exporta uma visualização para PDF"""
    try:
        # Salvar como arquivo temporário
        temp_file = f"temp_{os.path.basename(filename)}"
        fig.write_image(temp_file, format="pdf")
        
        # Ler arquivo
        with open(temp_file, "rb") as f:
            pdf_data = f.read()
        
        # Excluir arquivo temporário
        os.remove(temp_file)
        
        # Retornar para download
        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        pdf_link = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{filename}">Clique para baixar</a>'
        st.markdown(pdf_link, unsafe_allow_html=True)
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao exportar visualização: {str(e)}")
        return False

def suggest_visualization(df):
    """Sugere o melhor tipo de visualização com base nos dados"""
    
    if df.empty or len(df.columns) < 2:
        return None, None, None
    
    # Identificar os tipos de colunas
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    
    suggestion = {}
    
    # Para série temporal
    if date_cols and numeric_cols:
        suggestion["Linhas"] = {"x": date_cols[0], "y": numeric_cols[0]}
    
    # Para comparação de categorias
    if text_cols and numeric_cols:
        suggestion["Barras"] = {"x": text_cols[0], "y": numeric_cols[0]}
    
    # Para distribuição
    if numeric_cols:
        suggestion["Histograma"] = {"x": numeric_cols[0], "y": None}
    
    # Para proporções (se são poucos valores categóricos)
    if text_cols and numeric_cols and df[text_cols[0]].nunique() <= 10:
        suggestion["Pizza"] = {"x": text_cols[0], "y": numeric_cols[0]}
    
    # Para correlação
    if len(numeric_cols) >= 2:
        suggestion["Dispersão"] = {"x": numeric_cols[0], "y": numeric_cols[1]}
    
    if suggestion:
        # Pegar a primeira sugestão
        chart_type = list(suggestion.keys())[0]
        x_column = suggestion[chart_type]["x"]
        y_column = suggestion[chart_type]["y"]
        
        return chart_type, x_column, y_column
    
    return None, None, None

def create_dashboard(visualizations, layout):
    """Cria um dashboard com múltiplas visualizações"""
    pass  # Implementação avançada para versões futuras
