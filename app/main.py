import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import yaml
import base64

# Importação dos módulos do sistema
from auth import authenticate_user, create_user, is_authenticated
from database import connect_database, execute_query, test_connection
from nlp_engine import natural_to_sql, validate_query, improve_model
from visualizations import create_visualization, export_visualization
from utils import save_query, get_history, add_to_gold_list, get_gold_list
# Importar componentes UI customizados
from ui_components import (
    load_css, card, metric_card, styled_table, 
    styled_plotly_chart, notification, gradient_header, custom_button
)

# Configuração da página
st.set_page_config(
    page_title="NeoQuery AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Carregar CSS personalizado
load_css()
