def update_user(email, details):
    """Atualiza detalhes do usuário"""
    users = _get_users()
    
    if email not in users:
        return False
    
    # Atualiza apenas os campos permitidos
    allowed_fields = ["name", "company", "plan", "plan_expires"]
    
    for field in allowed_fields:
        if field in details:
            users[email][field] = details[field]
    
    # Se a senha estiver sendo atualizada
    if "password" in details:
        users[email]["password"] = _hash_password(details["password"])
    
    _save_users(users)
    return True

def change_password(email, current_password, new_password):
    """Altera a senha do usuário"""
    if not authenticate_user(email, current_password):
        return False
    
    users = _get_users()
    users[email]["password"] = _hash_password(new_password)
    _save_users(users)
    
    return True

def delete_user(email, password):
    """Exclui um usuário"""
    if not authenticate_user(email, password):
        return False
    
    users = _get_users()
    
    if email in users:
        del users[email]
        _save_users(users)
        return True
    
    return False
