# modules/data_protection.py
import re
import pandas as pd
import hashlib
import base64
from typing import Dict, Any, List, Optional
import sys
import os

# Adicionar o diretório pai ao path para importar config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security_config import get_security_config

class DataProtector:
    def __init__(self, encryption_key: str = None):
        """
        Inicializa o protetor de dados
        
        Args:
            encryption_key: Chave para criptografia de dados sensíveis
        """
        self.encryption_key = encryption_key or get_security_config("ENCRYPTION_KEY")
        self.sensitive_patterns = get_security_config("SENSITIVE_DATA_PATTERNS", {})
    
    def sanitize_input(self, input_text: str) -> str:
        """
        Sanitiza a entrada do usuário para prevenir injeção SQL e outros ataques
        
        Args:
            input_text: Texto de entrada do usuário
            
        Returns:
            Texto sanitizado
        """
        # Remover caracteres de controle
        clean_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_text)
        
        # Remover comentários SQL
        clean_text = re.sub(r'--.*?$|/\*.*?\*/', '', clean_text, flags=re.MULTILINE)
        
        # Limitar o tamanho da entrada
        max_size = get_security_config("MAX_QUERY_SIZE", 10000)
        if len(clean_text) > max_size:
            clean_text = clean_text[:max_size]
            
        return clean_text
    
    def detect_sensitive_data(self, text: str) -> Optional[Dict[str, List[str]]]:
        """
        Detecta dados sensíveis em um texto
        
        Args:
            text: Texto para verificação
            
        Returns:
            Dicionário com tipos e ocorrências de dados sensíveis encontrados
        """
        if not text or not isinstance(text, str):
            return None
        
        results = {}
        
        # Verifica cada padrão de dados sensíveis
        for data_type, pattern in self.sensitive_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                results[data_type] = matches
                
        return results if results else None
    
    def anonymize_data(self, df: pd.DataFrame, 
                      columns_to_anonymize: Dict[str, str]) -> pd.DataFrame:
        """
        Anonimiza dados sensíveis em um DataFrame
        
        Args:
            df: DataFrame contendo dados potencialmente sensíveis
            columns_to_anonymize: Dicionário mapeando colunas ao método de anonimização
                                 ('hash', 'mask', 'tokenize')
            
        Returns:
            DataFrame com dados anonimizados
        """
        df_copy = df.copy()
        
        for col, method in columns_to_anonymize.items():
            if col not in df_copy.columns:
                continue
                
            if method == 'mask':
                # Máscara simples para dados sensíveis (ex: e***@***.com)
                df_copy[col] = df_copy[col].astype(str).apply(self._mask_data)
                
            elif method == 'hash':
                # Hash para dados que precisam ser consistentes
                df_copy[col] = df_copy[col].astype(str).apply(self._hash_data)
                
            elif method == 'tokenize':
                # Tokenização para dados que precisam ser reversíveis
                df_copy[col] = df_copy[col].astype(str).apply(self._tokenize_data)
                
        return df_copy
    
    def _mask_data(self, text: str) -> str:
        """
        Mascara um texto sensível
        
        Args:
            text: Texto para mascarar
            
        Returns:
            Texto mascarado
        """
        if not text or text == 'nan':
            return text
            
        # Diferentes máscaras baseadas no tipo de dado
        if '@' in text:  # Email
            username, domain = text.split('@', 1)
            domain_parts = domain.split('.')
            return f"{username[0]}{'*' * (len(username)-1)}@{'*' * len(domain_parts[0])}.{domain_parts[-1]}"
            
        elif re.search(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', text):  # CPF
            return re.sub(r'(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})', r'\1.***.***-**', text)
            
        elif re.search(r'(\(?\d{2}\)?\s?)(\d{4,5}\-?\d{4})', text):  # Telefone
            return re.sub(r'(\(?\d{2}\)?\s?)(\d{4,5}\-?\d{4})', r'\1****-**\3\4', text)
            
        else:  # Geral
            if len(text) <= 2:
                return text
            return text[0] + '*' * (len(text) - 2) + text[-1]
    
    def _hash_data(self, text: str) -> str:
        """
        Gera um hash para um texto sensível
        
        Args:
            text: Texto para hash
            
        Returns:
            Hash do texto
        """
        if not text or text == 'nan':
            return text
            
        # Gera um hash SHA-256 e retorna os primeiros 8 caracteres
        hash_obj = hashlib.sha256((text + self.encryption_key).encode())
        return hash_obj.hexdigest()[:8]
    
    def _tokenize_data(self, text: str) -> str:
        """
        Tokeniza um texto sensível (reversível com a chave)
        
        Args:
            text: Texto para tokenizar
            
        Returns:
            Texto tokenizado
        """
        if not text or text == 'nan':
            return text
            
        # Implementação simples de tokenização usando base64
        token = base64.b64encode(
            hashlib.pbkdf2_hmac(
                'sha256', 
                text.encode(), 
                self.encryption_key.encode(), 
                100000
            )
        ).decode('utf-8')
        
        return f"TOK_{token[:12]}"
    
    def audit_query(self, query: str) -> Dict[str, Any]:
        """
        Audita uma consulta para avaliar riscos de segurança
        
        Args:
            query: Consulta a ser auditada
            
        Returns:
            Resultado da auditoria com nível de risco e alertas
        """
        query_lower = query.lower()
        result = {
            "risk_level": "low",
            "alerts": []
        }
        
        # Palavras que podem indicar dados sensíveis
        sensitive_keywords = [
            'senha', 'password', 'credit', 'credito', 'cpf', 'cnpj', 'rg', 
            'secret', 'token', 'auth', 'private', 'confidential', 'ssn'
        ]
        
        # Verificar se contém palavras-chave sensíveis
        for keyword in sensitive_keywords:
            if keyword in query_lower:
                result["risk_level"] = "medium"
                result["alerts"].append(f"Possível acesso a dados sensíveis: '{keyword}'")
        
        # Verificar padrões de uso suspeito
        if 'select *' in query_lower:
            result["alerts"].append("Consulta retorna todas as colunas, pode expor dados sensíveis")
            if result["risk_level"] == "low":
                result["risk_level"] = "medium"
        
        # Verificar acesso a tabelas potencialmente sensíveis
        sensitive_tables = ['user', 'customer', 'employee', 'payment', 'credit', 'account']
        for table in sensitive_tables:
            if re.search(r'\b' + table + r'\b', query_lower):
                result["alerts"].append(f"Acesso à tabela potencialmente sensível: '{table}'")
                if result["risk_level"] == "low":
                    result["risk_level"] = "medium"
        
        # Se há muitos alertas, aumentar o nível de risco
        if len(result["alerts"]) >= 3:
            result["risk_level"] = "high"
            
        return result

