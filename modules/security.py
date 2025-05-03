# modules/security.py
import jwt
import datetime
import time
import logging
import os
from typing import Dict, Any, Optional, List
import sys

# Adicionar o diretório pai ao path para importar config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security_config import get_security_config

class SecurityManager:
    def __init__(self, secret_key: str = None):
        """
        Inicializa o gerenciador de segurança
        
        Args:
            secret_key: Chave secreta para JWT (opcional)
        """
        self.secret_key = secret_key or get_security_config("JWT_SECRET_KEY")
        self.failed_logins = {}  # Registra tentativas falhas de login
        self.session_timeout = get_security_config("SESSION_TIMEOUT", 3600)  # segundos
        
        # Configurar logging
        log_level = get_security_config("LOG_LEVEL", "INFO")
        numeric_level = getattr(logging, log_level.upper(), None)
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()],
            force=True
        )
        self.logger = logging.getLogger("security")
        self.audit_logger = logging.getLogger("audit")
        
    def generate_token(self, user_data: Dict[str, Any]) -> str:
        """
        Gera um token JWT para um usuário
        
        Args:
            user_data: Dados do usuário a serem incluídos no token
            
        Returns:
            Token JWT assinado
        """
        if not user_data.get('username'):
            raise ValueError("O nome de usuário é obrigatório")
            
        # Adicionar campos obrigatórios
        payload = {
            'username': user_data['username'],
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=self.session_timeout)
        }
        
        # Adicionar campos extras
        for key, value in user_data.items():
            if key != 'username' and key != 'iat' and key != 'exp':
                payload[key] = value
                
        # Assinar o token
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Registrar a ação
        self.log_activity(user_data['username'], "token_generation", "security", "success")
        
        return token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Valida um token JWT
        
        Args:
            token: Token JWT a ser validado
            
        Returns:
            Dados do usuário contidos no token
            
        Raises:
            Exception: Se o token for inválido ou expirado
        """
        try:
            # Verificar e decodificar o token
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Verificar a validade temporal
            if 'exp' in payload and datetime.datetime.fromtimestamp(payload['exp']) < datetime.datetime.utcnow():
                raise Exception("Token expirado")
                
            # Registrar a validação
            if 'username' in payload:
                self.log_activity(payload['username'], "token_validation", "security", "success")
                
            return payload
            
        except jwt.ExpiredSignatureError:
            self.log_activity("unknown", "token_validation", "security", "failed", "Token expirado")
            raise Exception("Token expirado")
            
        except jwt.InvalidTokenError:
            self.log_activity("unknown", "token_validation", "security", "failed", "Token inválido")
            raise Exception("Token inválido")
            
        except Exception as e:
            self.log_activity("unknown", "token_validation", "security", "failed", str(e))
            raise Exception(f"Erro ao validar token: {str(e)}")
    
    def check_login_attempts(self, username: str) -> bool:
        """
        Verifica se um usuário pode tentar fazer login
        
        Args:
            username: Nome do usuário
            
        Returns:
            True se o usuário pode tentar login, False se está bloqueado
        """
        if username not in self.failed_logins:
            return True
            
        max_attempts = get_security_config("FAILED_LOGIN_ATTEMPTS", 5)
        lockout_time = get_security_config("ACCOUNT_LOCKOUT_TIME", 900)  # segundos
        
        attempts = self.failed_logins[username]['attempts']
        last_attempt = self.failed_logins[username]['timestamp']
        
        # Se o número de tentativas excedeu o limite
        if attempts >= max_attempts:
            # Verificar se já passou o tempo de bloqueio
            if time.time() - last_attempt >= lockout_time:
                # Reset contador após tempo de bloqueio
                self.failed_logins[username]['attempts'] = 0
                return True
            else:
                # Ainda está bloqueado
                return False
                
        return True
    
    def record_failed_login(self, username: str) -> None:
        """
        Registra uma tentativa falha de login
        
        Args:
            username: Nome do usuário
        """
        if username not in self.failed_logins:
            self.failed_logins[username] = {
                'attempts': 1,
                'timestamp': time.time()
            }
        else:
            self.failed_logins[username]['attempts'] += 1
            self.failed_logins[username]['timestamp'] = time.time()
            
        # Registrar a ação
        self.log_activity(username, "login", "security", "failed", 
                         f"Tentativa {self.failed_logins[username]['attempts']}")
    
    def reset_failed_logins(self, username: str) -> None:
        """
        Reseta o contador de tentativas falhas de login
        
        Args:
            username: Nome do usuário
        """
        if username in self.failed_logins:
            self.failed_logins[username]['attempts'] = 0
    
    def log_activity(self, user: str, action: str, module: str, 
                    status: str, details: str = "") -> None:
        """
        Registra uma atividade para fins de auditoria
        
        Args:
            user: Nome do usuário
            action: Ação realizada
            module: Módulo onde a ação ocorreu
            status: Status da ação (success, failed, etc.)
            details: Detalhes adicionais
        """
        if not get_security_config("ENABLE_AUDIT_LOGS", True):
            return
            
        message = f"USER:{user} | ACTION:{action} | MODULE:{module} | STATUS:{status}"
        if details:
            message += f" | DETAILS:{details}"
            
        if status == "failed":
            self.audit_logger.warning(message)
        else:
            self.audit_logger.info(message)
