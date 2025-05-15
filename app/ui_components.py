import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import base64
from datetime import datetime

# Função para carregar CSS
def load_css():
    """Carrega o CSS personalizado."""
    try:
        with open('static/css/theme.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        # Tenta caminho alternativo
        try:
            with open('../static/css/theme.css') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Não foi possível carregar o CSS: {e}")

# Componentes de UI modernos
def card(title, content, icon=None):
    """Cria um card estilizado."""
    icon_html = f'<i class="fas fa-{icon}"></i> ' if icon else ''
    return f"""
    <div class="card">
        <div class="card-header">
            {icon_html}{title}
        </div>
        <div class="card-body">
            {content}
        </div>
    </div>
    """

def metric_card(label, value, delta=None, delta_color="normal"):
    """Cria um card de métrica estilizado."""
    delta_html = ""
    if delta is not None:
        direction = "up" if delta >= 0 else "down"
        delta_html = f"""
        <div class="metric-delta metric-delta-{direction}" style="color: {'green' if delta_color == 'good' else 'red' if delta_color == 'bad' else 'inherit'}">
            <i class="fas fa-arrow-{direction}"></i> {abs(delta)}%
        </div>
        """
    
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def styled_table(df):
    """Cria uma tabela estilizada a partir de um DataFrame."""
    table_html = '<table class="styled-table"><thead><tr>'
    
    # Cabeçalhos
    for col in df.columns:
        table_html += f'<th>{col}</th>'
    table_html += '</tr></thead><tbody>'
    
    # Linhas
    for _, row in df.iterrows():
        table_html += '<tr>'
        for col in df.columns:
            table_html += f'<td>{row[col]}</td>'
        table_html += '</tr>'
    
    table_html += '</tbody></table>'
    return table_html

def styled_plotly_chart(fig):
    """Aplica estilo consistente a um gráfico Plotly."""
    fig.update_layout(
        template="none",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Roboto, sans-serif", size=14),
        title=dict(font=dict(size=20, family="Roboto, sans-serif")),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig

def notification(message, type="info"):
    """Cria uma notificação estilizada."""
    if type == "success":
        return f'<div class="success-box">{message}</div>'
    elif type == "warning":
        return f'<div class="warning-box">{message}</div>'
    elif type == "error":
        return f'<div class="error-box">{message}</div>'
    else:
        return f'<div class="info-box">{message}</div>'

def gradient_header(title, subtitle=None):
    """Cria um cabeçalho com gradiente."""
    subtitle_html = f'<p class="header-subtitle">{subtitle}</p>' if subtitle else ''
    return f"""
    <div class="gradient-header animate-fade-in">
        <h1>{title}</h1>
        {subtitle_html}
    </div>
    """

def custom_button(label, icon=None, key=None):
    """Cria um botão customizado com ícone."""
    button_id = f"btn_{key}" if key else f"btn_{label.lower().replace(' ', '_')}"
    icon_html = f'<i class="fas fa-{icon}"></i> ' if icon else ''
    
    html = f"""
    <button id="{button_id}" class="custom-button">
        {icon_html}{label}
    </button>
    """
    
    return html
