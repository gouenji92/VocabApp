import os
import json
import hashlib
from typing import Optional, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

os.makedirs(DATA_DIR, exist_ok=True)

def _load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        return json.loads(open(USERS_FILE, 'r', encoding='utf-8').read())
    except Exception:
        return []

def _save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str, email: str = None) -> Dict[str, Any]:
    users = _load_users()
    if any(u['username'] == username for u in users):
        raise ValueError('Username already exists')
    
    user = {
        'username': username,
        'password_hash': hash_password(password),
        'email': email,
        'display_name': username,
        'avatar': None,
    }
    users.append(user)
    _save_users(users)
    return {
        'username': username,
        'email': email,
        'display_name': username,
        'avatar': None,
    }

def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    users = _load_users()
    for u in users:
        if u['username'] == username and u['password_hash'] == hash_password(password):
            return {
                'username': username,
                'email': u.get('email'),
                'display_name': u.get('display_name') or username,
                'avatar': u.get('avatar')
            }
    return None

def get_user(username: str) -> Optional[Dict[str, Any]]:
    users = _load_users()
    for u in users:
        if u['username'] == username:
            return {
                'username': username,
                'email': u.get('email'),
                'display_name': u.get('display_name') or username,
                'avatar': u.get('avatar')
            }
    return None

def update_user_profile(username: str, display_name: Optional[str] = None, email: Optional[str] = None, avatar: Optional[str] = None) -> Optional[Dict[str, Any]]:
    users = _load_users()
    for i, u in enumerate(users):
        if u.get('username') == username:
            if display_name is not None and display_name.strip():
                u['display_name'] = display_name.strip()
            if email is not None:
                u['email'] = email
            if avatar is not None:
                u['avatar'] = avatar
            users[i] = u
            _save_users(users)
            return {
                'username': username,
                'email': u.get('email'),
                'display_name': u.get('display_name') or username,
                'avatar': u.get('avatar')
            }
    return None

def change_user_password(username: str, current_password: str, new_password: str) -> bool:
    users = _load_users()
    for i, u in enumerate(users):
        if u.get('username') == username:
            # verify current password
            if u.get('password_hash') != hash_password(current_password):
                return False
            u['password_hash'] = hash_password(new_password)
            users[i] = u
            _save_users(users)
            return True
    return False
