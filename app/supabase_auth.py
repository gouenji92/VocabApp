from .auth import *import hashlib
from typing import Any, Dict, Optional

from .db import UserModel, session_scope, utc_now_iso


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _user_to_dict(user: UserModel) -> Dict[str, Any]:
    return {
        'username': user.username,
        'email': user.email,
        'display_name': user.display_name or user.username,
        'avatar': user.avatar,
        'cover_image': user.cover_image,
        'bio': user.bio or '',
        'location': user.location or '',
        'website': user.website or '',
        'facebook': user.facebook or '',
        'instagram': user.instagram or '',
        'twitter': user.twitter or '',
        'school': user.school or '',
        'joined_date': user.joined_date,
        'followers': user.followers or [],
        'following': user.following or [],
    }


def create_user(username: str, password: str, email: str = None) -> Dict[str, Any]:
    with session_scope() as session:
        if session.get(UserModel, username):
            raise ValueError('Username already exists')

        user = UserModel(
            username=username,
            password_hash=hash_password(password),
            email=email,
            display_name=username,
            avatar=None,
            cover_image=None,
            bio='',
            location='',
            website='',
            facebook='',
            instagram='',
            twitter='',
            school='',
            joined_date=utc_now_iso(),
            followers=[],
            following=[],
        )
        session.add(user)
        session.flush()
        return _user_to_dict(user)


def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    with session_scope() as session:
        user = session.get(UserModel, username)
        if user and user.password_hash == hash_password(password):
            return _user_to_dict(user)
    return None


def get_user(username: str) -> Optional[Dict[str, Any]]:
    with session_scope() as session:
        user = session.get(UserModel, username)
        if user:
            return _user_to_dict(user)
    return None


def update_user_profile(username: str, display_name: Optional[str] = None, email: Optional[str] = None, avatar: Optional[str] = None, cover_image: Optional[str] = None, bio: Optional[str] = None, location: Optional[str] = None, website: Optional[str] = None, facebook: Optional[str] = None, instagram: Optional[str] = None, twitter: Optional[str] = None, school: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with session_scope() as session:
        user = session.get(UserModel, username)
        if not user:
            return None

        if display_name is not None and display_name.strip():
            user.display_name = display_name.strip()
        if email is not None:
            user.email = email
        if avatar is not None:
            user.avatar = avatar
        if cover_image is not None:
            user.cover_image = cover_image
        if bio is not None:
            user.bio = bio
        if location is not None:
            user.location = location
        if website is not None:
            user.website = website
        if facebook is not None:
            user.facebook = facebook
        if instagram is not None:
            user.instagram = instagram
        if twitter is not None:
            user.twitter = twitter
        if school is not None:
            user.school = school

        session.add(user)
        session.flush()
        return _user_to_dict(user)


def change_user_password(username: str, current_password: str, new_password: str) -> bool:
    with session_scope() as session:
        user = session.get(UserModel, username)
        if not user or user.password_hash != hash_password(current_password):
            return False
        user.password_hash = hash_password(new_password)
        session.add(user)
        return True


def follow_user(follower_username: str, following_username: str) -> bool:
    with session_scope() as session:
        follower = session.get(UserModel, follower_username)
        following = session.get(UserModel, following_username)
        if not follower or not following:
            return False

        follower_following = list(follower.following or [])
        following_followers = list(following.followers or [])

        if following_username not in follower_following:
            follower_following.append(following_username)
        if follower_username not in following_followers:
            following_followers.append(follower_username)

        follower.following = follower_following
        following.followers = following_followers
        session.add_all([follower, following])
        return True


def unfollow_user(follower_username: str, following_username: str) -> bool:
    with session_scope() as session:
        follower = session.get(UserModel, follower_username)
        following = session.get(UserModel, following_username)
        if not follower or not following:
            return False

        follower_following = list(follower.following or [])
        following_followers = list(following.followers or [])

        if following_username in follower_following:
            follower_following.remove(following_username)
        if follower_username in following_followers:
            following_followers.remove(follower_username)

        follower.following = follower_following
        following.followers = following_followers
        session.add_all([follower, following])
        return True


def is_following(follower_username: str, following_username: str) -> bool:
    user = get_user(follower_username)
    if not user:
        return False
    return following_username in user.get('following', [])


def get_followers(username: str) -> list:
    user = get_user(username)
    if not user:
        return []
    return user.get('followers', [])


def get_following(username: str) -> list:
    user = get_user(username)
    if not user:
        return []
    return user.get('following', [])
