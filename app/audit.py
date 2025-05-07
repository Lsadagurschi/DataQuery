import os
import json
from datetime import datetime

AUDIT_LOG_FILE = "audit_log.json"

def log_event(event_type, user_email, details):
    """Registra um evento no log de auditoria"""
    
    logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, 'r') as f:
                logs = json.load(f)
        except:
            logs = []
    
    # Adicionar novo registro
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user_email": user_email,
        "ip_address": "127.0.0.1",  # Em produção, usar o IP real
        "details": details
    }
    
    logs.append(log_entry)
    
    with open(AUDIT_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)
