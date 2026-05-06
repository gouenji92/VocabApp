"""Placeholder for database initialization (using JSON storage)"""

def init_db():
    """Initialize database - with JSON storage, just ensure data directory exists"""
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
import os
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_SQLITE_PATH = os.path.join(DATA_DIR, 'vocabapp.db')
DATABASE_URL = os.getenv('DATABASE_URL') or f'sqlite:///{DEFAULT_SQLITE_PATH}'

engine_kwargs = {'future': True, 'pool_pre_ping': True}
if DATABASE_URL.startswith('sqlite'):
    engine_kwargs['connect_args'] = {'check_same_thread': False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
Base = declarative_base()


class UserModel(Base):
    __tablename__ = 'users'

    username = Column(String(255), primary_key=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    avatar = Column(String(1024), nullable=True)
    cover_image = Column(String(1024), nullable=True)
    bio = Column(Text, nullable=True, default='')
    location = Column(Text, nullable=True, default='')
    website = Column(Text, nullable=True, default='')
    facebook = Column(Text, nullable=True, default='')
    instagram = Column(Text, nullable=True, default='')
    twitter = Column(Text, nullable=True, default='')
    school = Column(Text, nullable=True, default='')
    joined_date = Column(String(64), nullable=True)
    followers = Column(JSON, nullable=False, default=list)
    following = Column(JSON, nullable=False, default=list)


class VocabSetModel(Base):
    __tablename__ = 'vocab_sets'

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language_from = Column(String(32), nullable=False, default='en')
    language_to = Column(String(32), nullable=False, default='vi')
    user_id = Column(String(255), nullable=True, index=True)
    visibility = Column(String(32), nullable=False, default='private')
    owner_username = Column(String(255), nullable=True, index=True)
    created_at = Column(String(64), nullable=False)


class TermModel(Base):
    __tablename__ = 'terms'

    id = Column(String(36), primary_key=True)
    set_id = Column(String(36), ForeignKey('vocab_sets.id', ondelete='CASCADE'), nullable=False, index=True)
    term = Column(String(255), nullable=False)
    definition = Column(Text, nullable=False)
    pos = Column(String(255), nullable=True)
    pronunciation = Column(String(255), nullable=True)
    example = Column(Text, nullable=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=True)


class ProgressModel(Base):
    __tablename__ = 'progress'

    id = Column(String(36), primary_key=True)
    term_id = Column(String(36), ForeignKey('terms.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    easiness = Column(Float, nullable=False, default=2.5)
    repetitions = Column(Integer, nullable=False, default=0)
    interval_days = Column(Integer, nullable=False, default=1)
    next_review = Column(String(64), nullable=False)
    last_review = Column(String(64), nullable=True)

    __table_args__ = (UniqueConstraint('term_id', 'user_id', name='uq_progress_term_user'),)


class LikeModel(Base):
    __tablename__ = 'likes'

    id = Column(String(36), primary_key=True)
    set_id = Column(String(36), ForeignKey('vocab_sets.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint('set_id', 'user_id', name='uq_like_set_user'),)


class CommentModel(Base):
    __tablename__ = 'comments'

    id = Column(String(36), primary_key=True)
    set_id = Column(String(36), ForeignKey('vocab_sets.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    username = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(String(64), nullable=False)
    edited_at = Column(String(64), nullable=True)


class ShareModel(Base):
    __tablename__ = 'shares'

    id = Column(String(36), primary_key=True)
    set_id = Column(String(36), ForeignKey('vocab_sets.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(String(64), nullable=False)


class PostModel(Base):
    __tablename__ = 'posts'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    attached_set_id = Column(String(36), nullable=True, index=True)
    image_url = Column(String(1024), nullable=True)
    created_at = Column(String(64), nullable=False)
    edited_at = Column(String(64), nullable=True)
    post_type = Column(String(64), nullable=False, default='text_post')


class BookmarkModel(Base):
    __tablename__ = 'bookmarks'

    id = Column(String(36), primary_key=True)
    set_id = Column(String(36), ForeignKey('vocab_sets.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint('set_id', 'user_id', name='uq_bookmark_set_user'),)


class CommentLikeModel(Base):
    __tablename__ = 'comment_likes'

    id = Column(String(36), primary_key=True)
    comment_id = Column(String(36), ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint('comment_id', 'user_id', name='uq_comment_like_comment_user'),)


class CommentReplyModel(Base):
    __tablename__ = 'comment_replies'

    id = Column(String(36), primary_key=True)
    comment_id = Column(String(36), ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    username = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(String(64), nullable=False)
    edited_at = Column(String(64), nullable=True)


class ReplyLikeModel(Base):
    __tablename__ = 'reply_likes'

    id = Column(String(36), primary_key=True)
    reply_id = Column(String(36), ForeignKey('comment_replies.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint('reply_id', 'user_id', name='uq_reply_like_reply_user'),)


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


_db_initialized = False

def init_db() -> None:
    """Initialize database tables. Called on app startup."""
    global _db_initialized
    if _db_initialized:
        return
    try:
        Base.metadata.create_all(bind=engine)
        _db_initialized = True
        print("[INFO] Database tables initialized successfully")
    except Exception as e:
        print(f"[WARN] Database initialization error: {e}")
        # Don't raise - will retry on next request
