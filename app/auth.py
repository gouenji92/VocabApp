import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from .storage import _load, _save, USERS_FILE


def hash_password(password: str) -> str:
	return hashlib.sha256(password.encode()).hexdigest()


def _user_to_dict(user: Dict[str, Any]) -> Dict[str, Any]:
	return {
		'username': user.get('username'),
		'email': user.get('email', ''),
		'display_name': user.get('display_name') or user.get('username'),
		'avatar': user.get('avatar'),
		'cover_image': user.get('cover_image'),
		'bio': user.get('bio', ''),
		'location': user.get('location', ''),
		'website': user.get('website', ''),
		'facebook': user.get('facebook', ''),
		'instagram': user.get('instagram', ''),
		'twitter': user.get('twitter', ''),
		'school': user.get('school', ''),
		'joined_date': user.get('joined_date'),
		'followers': user.get('followers', []) or [],
		'following': user.get('following', []) or [],
	}


def _load_users() -> List[Dict[str, Any]]:
	return _load(USERS_FILE)


def _save_users(users: List[Dict[str, Any]]) -> None:
	_save(USERS_FILE, users)


def _find_user_index(users: List[Dict[str, Any]], username: str) -> int:
	for index, user in enumerate(users):
		if user.get('username') == username:
			return index
	return -1


def create_user(username: str, password: str, email: str = None) -> Dict[str, Any]:
	users = _load_users()
	if _find_user_index(users, username) != -1:
		raise ValueError('Username already exists')

	now = datetime.utcnow().isoformat()
	user = {
		'username': username,
		'password_hash': hash_password(password),
		'email': email or '',
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
		'joined_date': now,
		'followers': [],
		'following': [],
	}
	users.append(user)
	_save_users(users)
	return _user_to_dict(user)


def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
	users = _load_users()
	for user in users:
		if user.get('username') == username and user.get('password_hash') == hash_password(password):
			return _user_to_dict(user)
	return None


def get_user(username: str) -> Optional[Dict[str, Any]]:
	users = _load_users()
	for user in users:
		if user.get('username') == username:
			return _user_to_dict(user)
	return None


def update_user_profile(
	username: str,
	display_name: Optional[str] = None,
	email: Optional[str] = None,
	avatar: Optional[str] = None,
	cover_image: Optional[str] = None,
	bio: Optional[str] = None,
	location: Optional[str] = None,
	website: Optional[str] = None,
	facebook: Optional[str] = None,
	instagram: Optional[str] = None,
	twitter: Optional[str] = None,
	school: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
	users = _load_users()
	index = _find_user_index(users, username)
	if index == -1:
		return None

	user = users[index]

	if display_name is not None and display_name.strip():
		user['display_name'] = display_name.strip()
	if email is not None:
		user['email'] = email
	if avatar is not None:
		user['avatar'] = avatar
	if cover_image is not None:
		user['cover_image'] = cover_image
	if bio is not None:
		user['bio'] = bio
	if location is not None:
		user['location'] = location
	if website is not None:
		user['website'] = website
	if facebook is not None:
		user['facebook'] = facebook
	if instagram is not None:
		user['instagram'] = instagram
	if twitter is not None:
		user['twitter'] = twitter
	if school is not None:
		user['school'] = school

	users[index] = user
	_save_users(users)
	return _user_to_dict(user)


def change_user_password(username: str, current_password: str, new_password: str) -> bool:
	users = _load_users()
	index = _find_user_index(users, username)
	if index == -1:
		return False

	user = users[index]
	if user.get('password_hash') != hash_password(current_password):
		return False

	user['password_hash'] = hash_password(new_password)
	users[index] = user
	_save_users(users)
	return True


def follow_user(follower_username: str, following_username: str) -> bool:
	if follower_username == following_username:
		return False

	users = _load_users()
	follower_index = _find_user_index(users, follower_username)
	following_index = _find_user_index(users, following_username)
	if follower_index == -1 or following_index == -1:
		return False

	follower = users[follower_index]
	following = users[following_index]

	follower_following = list(follower.get('following', []) or [])
	following_followers = list(following.get('followers', []) or [])

	if following_username not in follower_following:
		follower_following.append(following_username)
	if follower_username not in following_followers:
		following_followers.append(follower_username)

	follower['following'] = follower_following
	following['followers'] = following_followers
	users[follower_index] = follower
	users[following_index] = following
	_save_users(users)
	return True


def unfollow_user(follower_username: str, following_username: str) -> bool:
	users = _load_users()
	follower_index = _find_user_index(users, follower_username)
	following_index = _find_user_index(users, following_username)
	if follower_index == -1 or following_index == -1:
		return False

	follower = users[follower_index]
	following = users[following_index]

	follower_following = list(follower.get('following', []) or [])
	following_followers = list(following.get('followers', []) or [])

	if following_username in follower_following:
		follower_following.remove(following_username)
	if follower_username in following_followers:
		following_followers.remove(follower_username)

	follower['following'] = follower_following
	following['followers'] = following_followers
	users[follower_index] = follower
	users[following_index] = following
	_save_users(users)
	return True


def is_following(follower_username: str, following_username: str) -> bool:
	user = get_user(follower_username)
	if not user:
		return False
	return following_username in user.get('following', [])


def get_followers(username: str) -> List[str]:
	user = get_user(username)
	if not user:
		return []
	return list(user.get('followers', []) or [])


def get_following(username: str) -> List[str]:
	user = get_user(username)
	if not user:
		return []
	return list(user.get('following', []) or [])


__all__ = [
	'hash_password',
	'create_user',
	'verify_user',
	'get_user',
	'update_user_profile',
	'change_user_password',
	'follow_user',
	'unfollow_user',
	'is_following',
	'get_followers',
	'get_following',
]
