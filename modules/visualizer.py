# modules/visualizer.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List
import sys
import os

# Adicionar o diretório pai ao path para importar config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import get_config
from modules.data_protection import DataProtector

class DataVisualizer:
    def __init__(self, data: pd.DataFrame):
        """
        Inicializa o visualizador de dados
        
        Args:
            data: DataFrame com os dados a serem visualizados
        """
        self.data = data
        self.default_chart_type = get_config("DEFAULT_CHART_TYPE", "bar")
        self.max_items = get_config("MAX_ITEMS_IN_CHART", 20)
        
    def suggest_visualization(self) -> go.Figure:
        """
        Sugere automaticamente uma visualização apropriada para os dados
        
        Returns:
            Figura Plotly com a visualização
        """
        # Se não há dados, retornar mensagem
        if self.data is None or len(self.data) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="Sem dados para visualizar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Limitar número de linhas para não sobrecarregar o gráfico
        display_data = self.data
        if len(display_data) > self.max_items:
            display_data = display_data.head(self.max_items)
        
        # Verificar as colunas para decidir o tipo de gráfico
        numeric_cols = display_data.select_dtypes(include=['number']).columns
        categorical_cols = display_data.select_dtypes(include=['object', 'category']).columns
        date_cols = display_data.select_dtypes(include=['datetime']).columns
        
        # Verificar se temos no mínimo uma coluna numérica
        if len(numeric_cols) == 0:
            # Se não tiver coluna numérica, fazer contagem de valores categóricos
            if len(categorical_cols) > 0:
                # Pegar a primeira coluna categórica
                cat_col = categorical_cols[0]
                counts = display_data[cat_col].value_counts().reset_index()
                counts.columns = [cat_col, 'count']
                
                return px.bar(
                    counts, 
                    x=cat_col, 
                    y='count', 
                    title=f'Contagem de {cat_col}',
                    labels={'count': 'Quantidade'}
                )
        
        # Se tiver pelo menos uma coluna numérica e uma categórica
        if len(numeric_cols) > 0 and len(categorical_cols) > 0:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            
            # Verificar se tem muitos valores únicos na coluna categórica
            if display_data[x_col].nunique() > self.max_items:
                # Se tiver muitos valores únicos, agrupar e mostrar os principais
                grouped = display_data.groupby(x_col)[y_col].sum().reset_index()
                grouped = grouped.sort_values(y_col, ascending=False).head(self.max_items)
                
                return px.bar(
                    grouped, 
                    x=x_col, 
                    y=y_col, 
                    title=f'{y_col} por {x_col} (Top {self.max_items})',
                    labels={y_col: y_col, x_col: x_col}
                )
            
            return px.bar(
                display_data, 
                x=x_col, 
                y=y_col,
                title=f'{y_col} por {x_col}',
                labels={y_col: y_col, x_col: x_col}
            )
        
        # Se tiver pelo menos uma coluna numérica e uma coluna de data
        elif len(numeric_cols) > 0 and len(date_cols) > 0:
            x_col = date_cols[0]
            y_col = numeric_cols[0]
            
            return px.line(
                display_data, 
                x=x_col, 
                y=y_col,
                title=f'{y_col} ao longo do tempo',
                labels={y_col: y_col, x_col: "Data"}
            )
            
        # Se tiver apenas colunas numéricas, usar scatter plot com as duas primeiras
        elif len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            return px.scatter(
                display_data, 
                x=x_col, 
                y=y_col,
                title=f'Relação entre {x_col} e {y_col}',
                labels={y_col: y_col, x_col: x_col}
            )
            
        # Se tiver apenas uma coluna numérica
        elif len(numeric_cols) == 1:
            y_col = numeric_cols[0]
            
            return px.histogram(
                display_data, 
                x=y_col,
                title=f'Distribuição de {y_col}',
                labels={y_col: y_col}
            )
            
        # Fallback: mostrar os dados em uma tabela
        return px.scatter(
            display_data.reset_index(), 
            x='index',
            title='Dados tabulares'
        )
    
    def create_custom_visualization(self, 
                                   chart_type: str, 
                                   x_axis: str, 
                                   y_axis: str) -> go.Figure:
        """
        Cria uma visualização customizada com base nas especificações
        
        Args:
            chart_type: Tipo de gráfico ('Barra', 'Linha', 'Dispersão', 'Pizza')
            x_axis: Nome da coluna para o eixo X
            y_axis: Nome da coluna para o eixo Y
            
        Returns:
            Figura Plotly com a visualização
        """
        # Se não há dados, retornar mensagem
        if self.data is None or len(self.data) == 0 or x_axis not in self.data.columns or y_axis not in self.data.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="Dados insuficientes para o gráfico solicitado",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Limitar número de linhas
        display_data = self.data
        if len(display_data) > self.max_items:
            display_data = display_data.head(self.max_items)
            
        # Criar gráfico com base no tipo solicitado
        if chart_type.lower() == 'barra':
            fig = px.bar(
                display_data, 
                x=x_axis, 
                y=y_axis,
                title=f'{y_axis} por {x_axis}',
                labels={y_axis: y_axis, x_axis: x_axis}
            )
        
        elif chart_type.lower() == 'linha':
            fig = px.line(
                display_data, 
                x=x_axis, 
                y=y_axis,
                title=f'{y_axis} por {x_axis}',
                labels={y_axis: y_axis, x_axis: x_axis}
            )
            
        elif chart_type.lower() == 'dispersão':
            fig = px.scatter(
                display_data, 
                x=x_axis, 
                y=y_axis,
                title=f'Relação entre {x_axis} e {y_axis}',
                labels={y_axis: y_axis, x_axis: x_axis}
            )
            
        elif chart_type.lower() == 'pizza':
            fig = px.pie(
                display_data,
                values=y_axis,
                names=x_axis,
                title=f'Distribuição de {y_axis} por {x_axis}'
            )
            
        else:
            # Tipo de gráfico não reconhecido, usar barra como padrão
            fig = px.bar(
                display_data, 
                x=x_axis, 
                y=y_axis,
                title=f'{y_axis} por {x_axis} (gráfico de barras)',
                labels={y_axis: y_axis, x_axis: x_axis}
            )
            
        return fig
    
    def visualize_with_privacy(self, data: pd.DataFrame) -> go.Figure:
        """
        Cria uma visualização com proteções adicionais de privacidade
        
        Args:
            data: DataFrame com os dados a serem visualizados
            
        Returns:
            Figura Plotly com a visualização
        """
        # Instanciar o protetor de dados
        data_protector = DataProtector()
        
        # Detectar colunas potencialmente sensíveis
        sensitive_columns = {}
        for col in data.columns:
            # Verificar apenas colunas de texto
            if data[col].dtype == 'object':
                # Amostragem para performance
                sample = data[col].dropna().head(5).astype(str).tolist()
                for value in sample:
                    detection = data_protector.detect_sensitive_data(value)
                    if detection:
                        # Encontrou dado sensível nesta coluna
                        sensitive_columns[col] = 'mask'
                        break
        
        # Anonimizar dados antes de visualizar
        if sensitive_columns:
            data = data_protector.anonymize_data(data, sensitive_columns)
        
        # Copiar o DataFrame original
        self.data = data
        
        # Usar o método padrão de visualização
        return self.suggest_visualization()
