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
        'cover_image': None,
        'bio': '',
        'location': '',
        'website': '',
        'facebook': '',
        'instagram': '',
        'twitter': '',
        'school': '',
        'joined_date': None,
        'followers': [],
        'following': [],
    }
    users.append(user)
    _save_users(users)
    return {
        'username': username,
        'email': email,
        'display_name': username,
        'avatar': None,
        'cover_image': None,
        'bio': '',
        'location': '',
        'website': '',
    }

def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    users = _load_users()
    for u in users:
        if u['username'] == username and u['password_hash'] == hash_password(password):
            return {
                'username': username,
                'email': u.get('email'),
                'display_name': u.get('display_name') or username,
                'avatar': u.get('avatar'),
                'cover_image': u.get('cover_image'),
                'bio': u.get('bio', ''),
                'location': u.get('location', ''),
                'website': u.get('website', ''),
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
                'avatar': u.get('avatar'),
                'cover_image': u.get('cover_image'),
                'bio': u.get('bio', ''),
                'location': u.get('location', ''),
                'website': u.get('website', ''),
                'joined_date': u.get('joined_date'),
                'followers': u.get('followers', []),
                'following': u.get('following', []),
            }
    return None

def update_user_profile(username: str, display_name: Optional[str] = None, email: Optional[str] = None, avatar: Optional[str] = None, cover_image: Optional[str] = None, bio: Optional[str] = None, location: Optional[str] = None, website: Optional[str] = None, facebook: Optional[str] = None, instagram: Optional[str] = None, twitter: Optional[str] = None, school: Optional[str] = None) -> Optional[Dict[str, Any]]:
    users = _load_users()
    for i, u in enumerate(users):
        if u.get('username') == username:
            if display_name is not None and display_name.strip():
                u['display_name'] = display_name.strip()
            if email is not None:
                u['email'] = email
            if avatar is not None:
                u['avatar'] = avatar
            if cover_image is not None:
                u['cover_image'] = cover_image
            if bio is not None:
                u['bio'] = bio
            if location is not None:
                u['location'] = location
            if website is not None:
                u['website'] = website
            if facebook is not None:
                u['facebook'] = facebook
            if instagram is not None:
                u['instagram'] = instagram
            if twitter is not None:
                u['twitter'] = twitter
            if school is not None:
                u['school'] = school
            users[i] = u
            _save_users(users)
            return {
                'username': username,
                'email': u.get('email'),
                'display_name': u.get('display_name') or username,
                'avatar': u.get('avatar'),
                'cover_image': u.get('cover_image'),
                'bio': u.get('bio', ''),
                'location': u.get('location', ''),
                'website': u.get('website', ''),
                'facebook': u.get('facebook', ''),
                'instagram': u.get('instagram', ''),
                'twitter': u.get('twitter', ''),
                'school': u.get('school', ''),
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

def follow_user(follower_username: str, following_username: str) -> bool:
    """Follower follows the following_username"""
    users = _load_users()
    follower_idx = None
    following_idx = None
    
    for i, u in enumerate(users):
        if u['username'] == follower_username:
            follower_idx = i
        if u['username'] == following_username:
            following_idx = i
    
    if follower_idx is None or following_idx is None:
        return False
    
    # Add to follower's following list
    if 'following' not in users[follower_idx]:
        users[follower_idx]['following'] = []
    if following_username not in users[follower_idx]['following']:
        users[follower_idx]['following'].append(following_username)
    
    # Add to following's followers list
    if 'followers' not in users[following_idx]:
        users[following_idx]['followers'] = []
    if follower_username not in users[following_idx]['followers']:
        users[following_idx]['followers'].append(follower_username)
    
    _save_users(users)
    return True

def unfollow_user(follower_username: str, following_username: str) -> bool:
    """Follower unfollows the following_username"""
    users = _load_users()
    follower_idx = None
    following_idx = None
    
    for i, u in enumerate(users):
        if u['username'] == follower_username:
            follower_idx = i
        if u['username'] == following_username:
            following_idx = i
    
    if follower_idx is None or following_idx is None:
        return False
    
    # Remove from follower's following list
    if 'following' in users[follower_idx] and following_username in users[follower_idx]['following']:
        users[follower_idx]['following'].remove(following_username)
    
    # Remove from following's followers list
    if 'followers' in users[following_idx] and follower_username in users[following_idx]['followers']:
        users[following_idx]['followers'].remove(follower_username)
    
    _save_users(users)
    return True

def is_following(follower_username: str, following_username: str) -> bool:
    """Check if follower is following following_username"""
    user = get_user(follower_username)
    if not user:
        return False
    return following_username in user.get('following', [])

def get_followers(username: str) -> list:
    """Get list of followers for a user"""
    user = get_user(username)
    if not user:
        return []
    return user.get('followers', [])

def get_following(username: str) -> list:
    """Get list of users that username is following"""
    user = get_user(username)
    if not user:
        return []
    return user.get('following', [])
