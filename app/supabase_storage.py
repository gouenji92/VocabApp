import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select

from .db import (
    BookmarkModel,
    CommentLikeModel,
    CommentModel,
    CommentReplyModel,
    LikeModel,
    PostModel,
    ProgressModel,
    ReplyLikeModel,
    ShareModel,
    TermModel,
    VocabSetModel,
    session_scope,
    utc_now_iso,
)


def _set_dict(row: VocabSetModel) -> Dict[str, Any]:
    return {
        'id': row.id,
        'name': row.name,
        'description': row.description,
        'language_from': row.language_from,
        'language_to': row.language_to,
        'user_id': row.user_id,
        'visibility': row.visibility,
        'owner_username': row.owner_username,
        'created_at': row.created_at,
    }


def _term_dict(row: TermModel) -> Dict[str, Any]:
    return {
        'id': row.id,
        'set_id': row.set_id,
        'term': row.term,
        'definition': row.definition,
        'pos': row.pos,
        'pronunciation': row.pronunciation,
        'example': row.example,
        'created_at': row.created_at,
        'updated_at': row.updated_at,
    }


def _progress_dict(row: ProgressModel) -> Dict[str, Any]:
    return {
        'id': row.id,
        'term_id': row.term_id,
        'user_id': row.user_id,
        'easiness': row.easiness,
        'repetitions': row.repetitions,
        'interval_days': row.interval_days,
        'next_review': row.next_review,
        'last_review': row.last_review,
    }


def _comment_dict(row: CommentModel) -> Dict[str, Any]:
    return {
        'id': row.id,
        'set_id': row.set_id,
        'user_id': row.user_id,
        'username': row.username,
        'content': row.content,
        'created_at': row.created_at,
        'edited_at': row.edited_at,
    }


def _post_dict(row: PostModel) -> Dict[str, Any]:
    return {
        'id': row.id,
        'user_id': row.user_id,
        'username': row.username,
        'content': row.content,
        'attached_set_id': row.attached_set_id,
        'image_url': row.image_url,
        'created_at': row.created_at,
        'edited_at': row.edited_at,
        'post_type': row.post_type or 'text_post',
    }


def _comment_reply_dict(row: CommentReplyModel) -> Dict[str, Any]:
    return {
        'id': row.id,
        'comment_id': row.comment_id,
        'user_id': row.user_id,
        'username': row.username,
        'content': row.content,
        'created_at': row.created_at,
        'edited_at': row.edited_at,
    }


def list_sets(user_id: str = None) -> List[Dict[str, Any]]:
    with session_scope() as session:
        query = select(VocabSetModel)
        if user_id:
            query = query.where(VocabSetModel.user_id == user_id)
        rows = session.execute(query).scalars().all()
        return [_set_dict(row) for row in rows]


def create_set(name: str, description: str, lang_from: str, lang_to: str, user_id: str = None, visibility: str = 'private', owner_username: str = None) -> Dict[str, Any]:
    with session_scope() as session:
        row = VocabSetModel(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            language_from=lang_from,
            language_to=lang_to,
            user_id=user_id,
            visibility=visibility,
            owner_username=owner_username,
            created_at=utc_now_iso(),
        )
        session.add(row)
        session.flush()
        return _set_dict(row)


def list_terms(set_id: str) -> List[Dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(TermModel).where(TermModel.set_id == set_id)).scalars().all()
        rows.sort(key=lambda item: item.created_at or '')
        return [_term_dict(row) for row in rows]


def add_term(set_id: str, term: str, definition: str, pos: str = None, pronunciation: str = None, example: str = None):
    with session_scope() as session:
        row = TermModel(
            id=str(uuid.uuid4()),
            set_id=set_id,
            term=term,
            definition=definition,
            pos=pos,
            pronunciation=pronunciation,
            example=example,
            created_at=utc_now_iso(),
            updated_at=None,
        )
        session.add(row)
        session.flush()
        return _term_dict(row)


def get_set(set_id: str) -> Dict[str, Any]:
    with session_scope() as session:
        row = session.get(VocabSetModel, set_id)
        return _set_dict(row) if row else None


def update_set(set_id: str, name: str = None, description: str = None, lang_from: str = None, lang_to: str = None, visibility: str = None) -> Dict[str, Any]:
    with session_scope() as session:
        row = session.get(VocabSetModel, set_id)
        if not row:
            return None
        if name is not None:
            row.name = name
        if description is not None:
            row.description = description
        if lang_from is not None:
            row.language_from = lang_from
        if lang_to is not None:
            row.language_to = lang_to
        if visibility is not None:
            row.visibility = visibility
        session.add(row)
        return _set_dict(row)


def delete_set(set_id: str):
    with session_scope() as session:
        term_ids = [row[0] for row in session.execute(select(TermModel.id).where(TermModel.set_id == set_id)).all()]
        comment_ids = [row[0] for row in session.execute(select(CommentModel.id).where(CommentModel.set_id == set_id)).all()]
        reply_ids = [row[0] for row in session.execute(select(CommentReplyModel.id).where(CommentReplyModel.comment_id.in_(comment_ids))).all()] if comment_ids else []

        if reply_ids:
            session.query(ReplyLikeModel).filter(ReplyLikeModel.reply_id.in_(reply_ids)).delete(synchronize_session=False)
            session.query(CommentReplyModel).filter(CommentReplyModel.id.in_(reply_ids)).delete(synchronize_session=False)

        if comment_ids:
            session.query(CommentLikeModel).filter(CommentLikeModel.comment_id.in_(comment_ids)).delete(synchronize_session=False)
            session.query(CommentModel).filter(CommentModel.id.in_(comment_ids)).delete(synchronize_session=False)

        if term_ids:
            session.query(ProgressModel).filter(ProgressModel.term_id.in_(term_ids)).delete(synchronize_session=False)
            session.query(TermModel).filter(TermModel.id.in_(term_ids)).delete(synchronize_session=False)

        session.query(LikeModel).filter(LikeModel.set_id == set_id).delete(synchronize_session=False)
        session.query(ShareModel).filter(ShareModel.set_id == set_id).delete(synchronize_session=False)
        session.query(BookmarkModel).filter(BookmarkModel.set_id == set_id).delete(synchronize_session=False)
        session.query(PostModel).filter(PostModel.attached_set_id == set_id).update({PostModel.attached_set_id: None}, synchronize_session=False)
        session.query(VocabSetModel).filter(VocabSetModel.id == set_id).delete(synchronize_session=False)


def delete_term(term_id: str):
    with session_scope() as session:
        session.query(ProgressModel).filter(ProgressModel.term_id == term_id).delete(synchronize_session=False)
        session.query(TermModel).filter(TermModel.id == term_id).delete(synchronize_session=False)


def update_term(term_id: str, term: str = None, definition: str = None, pos: str = None, example: str = None):
    with session_scope() as session:
        row = session.get(TermModel, term_id)
        if not row:
            return None
        if term is not None:
            row.term = term
        if definition is not None:
            row.definition = definition
        if pos is not None:
            row.pos = pos
        if example is not None:
            row.example = example
        row.updated_at = utc_now_iso()
        session.add(row)
        return _term_dict(row)


def get_term(term_id: str) -> Dict[str, Any]:
    with session_scope() as session:
        row = session.get(TermModel, term_id)
        return _term_dict(row) if row else None


def get_progress(term_id: str, user_id: str = 'default') -> Dict[str, Any]:
    with session_scope() as session:
        row = session.execute(select(ProgressModel).where(ProgressModel.term_id == term_id, ProgressModel.user_id == user_id)).scalars().first()
        return _progress_dict(row) if row else None


def save_progress(term_id: str, easiness: float, repetitions: int, interval: int, next_review: str, user_id: str = 'default'):
    with session_scope() as session:
        row = session.execute(select(ProgressModel).where(ProgressModel.term_id == term_id, ProgressModel.user_id == user_id)).scalars().first()
        if row is None:
            row = ProgressModel(
                id=str(uuid.uuid4()),
                term_id=term_id,
                user_id=user_id,
                easiness=easiness,
                repetitions=repetitions,
                interval_days=interval,
                next_review=next_review,
                last_review=utc_now_iso(),
            )
            session.add(row)
        else:
            row.easiness = easiness
            row.repetitions = repetitions
            row.interval_days = interval
            row.next_review = next_review
            row.last_review = utc_now_iso()
            session.add(row)


def list_progress(set_id: str, user_id: str = 'default') -> List[Dict[str, Any]]:
    with session_scope() as session:
        term_ids = [row[0] for row in session.execute(select(TermModel.id).where(TermModel.set_id == set_id)).all()]
        if not term_ids:
            return []
        rows = session.execute(select(ProgressModel).where(ProgressModel.term_id.in_(term_ids), ProgressModel.user_id == user_id)).scalars().all()
        return [_progress_dict(row) for row in rows]


def get_user_stats(user_id: str) -> Dict[str, Any]:
    sets = list_sets(user_id)
    all_terms = []
    for vocab_set in sets:
        all_terms.extend(list_terms(vocab_set['id']))

    with session_scope() as session:
        user_progs = session.execute(select(ProgressModel).where(ProgressModel.user_id == user_id)).scalars().all()

    total_words = len(all_terms)
    learned_words = len([prog for prog in user_progs if (prog.repetitions or 0) > 0])
    today = datetime.utcnow().date().isoformat()
    due_today = len([prog for prog in user_progs if (prog.next_review or '') <= today])

    if user_progs:
        avg_easiness = sum((prog.easiness or 2.5) for prog in user_progs) / len(user_progs)
        accuracy = min(100, max(0, (avg_easiness - 1.3) / (4.0 - 1.3) * 100))
    else:
        accuracy = 0

    review_dates = []
    for prog in user_progs:
        if prog.last_review:
            try:
                review_dates.append(datetime.fromisoformat(prog.last_review).date())
            except Exception:
                pass

    streak = 0
    if review_dates:
        review_dates = sorted(set(review_dates), reverse=True)
        current_date = datetime.utcnow().date()
        for review_date in review_dates:
            if (current_date - review_date).days <= 1:
                streak += 1
                current_date = review_date
            else:
                break

    return {
        'total_sets': len(sets),
        'total_words': total_words,
        'learned_words': learned_words,
        'due_today': due_today,
        'accuracy': round(accuracy, 1),
        'streak': streak,
    }


def list_public_sets(search: str = None, language_from: str = None, language_to: str = None) -> List[Dict[str, Any]]:
    with session_scope() as session:
        query = select(VocabSetModel).where(VocabSetModel.visibility == 'public')
        if search:
            search_lower = f'%{search.lower()}%'
            query = query.where((VocabSetModel.name.ilike(search_lower)) | (VocabSetModel.description.ilike(search_lower)))
        if language_from:
            query = query.where(VocabSetModel.language_from == language_from)
        if language_to:
            query = query.where(VocabSetModel.language_to == language_to)
        rows = session.execute(query).scalars().all()
        result = [_set_dict(row) for row in rows]
        for vocab_set in result:
            vocab_set['term_count'] = len(list_terms(vocab_set['id']))
        return result


def clone_set(set_id: str, new_user_id: str, new_username: str = None) -> Dict[str, Any]:
    original_set = get_set(set_id)
    if not original_set or original_set.get('visibility') != 'public':
        return None

    new_set = create_set(
        name=f"{original_set['name']} (Copy)",
        description=f"Copied from {original_set.get('owner_username', 'Unknown')}. {original_set.get('description', '')}",
        lang_from=original_set['language_from'],
        lang_to=original_set['language_to'],
        user_id=new_user_id,
        visibility='private',
        owner_username=new_username,
    )

    for term in list_terms(set_id):
        add_term(
            set_id=new_set['id'],
            term=term['term'],
            definition=term['definition'],
            pos=term.get('pos'),
            pronunciation=term.get('pronunciation'),
            example=term.get('example'),
        )

    return new_set


def add_like(set_id: str, user_id: str):
    with session_scope() as session:
        exists = session.execute(select(LikeModel).where(LikeModel.set_id == set_id, LikeModel.user_id == user_id)).scalars().first()
        if exists:
            return False
        session.add(LikeModel(id=str(uuid.uuid4()), set_id=set_id, user_id=user_id, created_at=utc_now_iso()))
        return True


def remove_like(set_id: str, user_id: str):
    with session_scope() as session:
        deleted = session.query(LikeModel).filter(LikeModel.set_id == set_id, LikeModel.user_id == user_id).delete(synchronize_session=False)
        return deleted > 0


def get_likes_count(set_id: str) -> int:
    with session_scope() as session:
        return session.query(LikeModel).filter(LikeModel.set_id == set_id).count()


def is_liked_by_user(set_id: str, user_id: str) -> bool:
    with session_scope() as session:
        return session.execute(select(LikeModel).where(LikeModel.set_id == set_id, LikeModel.user_id == user_id)).scalars().first() is not None


def add_comment(set_id: str, user_id: str, username: str, content: str) -> Dict[str, Any]:
    with session_scope() as session:
        row = CommentModel(id=str(uuid.uuid4()), set_id=set_id, user_id=user_id, username=username, content=content, created_at=utc_now_iso(), edited_at=None)
        session.add(row)
        session.flush()
        return _comment_dict(row)


def get_comments(set_id: str) -> List[Dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(CommentModel).where(CommentModel.set_id == set_id)).scalars().all()
        rows.sort(key=lambda item: item.created_at or '', reverse=True)
        return [_comment_dict(row) for row in rows]


def get_comments_count(set_id: str) -> int:
    with session_scope() as session:
        return session.query(CommentModel).filter(CommentModel.set_id == set_id).count()


def add_share(set_id: str, user_id: str):
    with session_scope() as session:
        session.add(ShareModel(id=str(uuid.uuid4()), set_id=set_id, user_id=user_id, created_at=utc_now_iso()))
        return True


def get_shares_count(set_id: str) -> int:
    with session_scope() as session:
        return session.query(ShareModel).filter(ShareModel.set_id == set_id).count()


def get_feed_posts(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(VocabSetModel).where(VocabSetModel.visibility == 'public')).scalars().all()
        rows.sort(key=lambda item: item.created_at or '', reverse=True)

    public_sets = [_set_dict(row) for row in rows]
    for vocab_set in public_sets:
        vocab_set['likes_count'] = get_likes_count(vocab_set['id'])
        vocab_set['comments_count'] = get_comments_count(vocab_set['id'])
        vocab_set['shares_count'] = get_shares_count(vocab_set['id'])
        terms = list_terms(vocab_set['id'])
        vocab_set['term_count'] = len(terms)
        vocab_set['preview_terms'] = terms[:3] if len(terms) > 3 else terms
        vocab_set['post_type'] = 'vocab_set'

    return public_sets[offset:offset + limit]


def create_post(user_id: str, username: str, content: str, attached_set_id: str = None, image_url: str = None) -> Dict[str, Any]:
    with session_scope() as session:
        row = PostModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            username=username,
            content=content,
            attached_set_id=attached_set_id,
            image_url=image_url,
            created_at=utc_now_iso(),
            edited_at=None,
            post_type='text_post',
        )
        session.add(row)
        session.flush()
        return _post_dict(row)


def list_all_feed_items(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    from .auth import get_user

    with session_scope() as session:
        posts = session.execute(select(PostModel)).scalars().all()
        public_sets = session.execute(select(VocabSetModel).where(VocabSetModel.visibility == 'public')).scalars().all()

    post_items = [_post_dict(row) for row in posts]
    for post in post_items:
        post['post_type'] = 'text_post'
        post['likes_count'] = get_likes_count(post['id'])
        post['comments_count'] = get_comments_count(post['id'])
        post['shares_count'] = get_shares_count(post['id'])
        user_info = get_user(post.get('username') or post.get('user_id'))
        if user_info:
            post['user_avatar'] = user_info.get('avatar')
            post['user_display_name'] = user_info.get('display_name') or post.get('username')
        if post.get('attached_set_id'):
            attached_set = get_set(post['attached_set_id'])
            if attached_set:
                terms = list_terms(attached_set['id'])
                attached_set['term_count'] = len(terms)
                attached_set['preview_terms'] = terms[:3] if len(terms) > 3 else terms
                post['attached_set'] = attached_set

    set_items = [_set_dict(row) for row in public_sets]
    for vocab_set in set_items:
        vocab_set['post_type'] = 'vocab_set'
        vocab_set['likes_count'] = get_likes_count(vocab_set['id'])
        vocab_set['comments_count'] = get_comments_count(vocab_set['id'])
        vocab_set['shares_count'] = get_shares_count(vocab_set['id'])
        terms = list_terms(vocab_set['id'])
        vocab_set['term_count'] = len(terms)
        vocab_set['preview_terms'] = terms[:3] if len(terms) > 3 else terms
        vocab_set['content'] = vocab_set.get('description', '')
        vocab_set['username'] = vocab_set.get('owner_username', 'Unknown')
        user_info = get_user(vocab_set.get('owner_username') or vocab_set.get('user_id'))
        if user_info:
            vocab_set['user_avatar'] = user_info.get('avatar')
            vocab_set['user_display_name'] = user_info.get('display_name') or vocab_set.get('username')

    all_items = post_items + set_items
    all_items.sort(key=lambda item: item.get('created_at', ''), reverse=True)
    return all_items[offset:offset + limit]


def get_user_posts(username: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(PostModel).where((PostModel.username == username) | (PostModel.user_id == username))).scalars().all()

    user_posts = [_post_dict(row) for row in rows]
    for post in user_posts:
        post['post_type'] = 'text_post'
        post['likes_count'] = get_likes_count(post['id'])
        post['comments_count'] = get_comments_count(post['id'])
        post['shares_count'] = get_shares_count(post['id'])
        if post.get('attached_set_id'):
            attached_set = get_set(post['attached_set_id'])
            if attached_set:
                terms = list_terms(attached_set['id'])
                attached_set['term_count'] = len(terms)
                attached_set['preview_terms'] = terms[:3] if len(terms) > 3 else terms
                post['attached_set'] = attached_set

    user_posts.sort(key=lambda item: item.get('created_at', ''), reverse=True)
    return user_posts[offset:offset + limit]


def add_bookmark(set_id: str, user_id: str) -> bool:
    with session_scope() as session:
        exists = session.execute(select(BookmarkModel).where(BookmarkModel.set_id == set_id, BookmarkModel.user_id == user_id)).scalars().first()
        if exists:
            return False
        session.add(BookmarkModel(id=str(uuid.uuid4()), set_id=set_id, user_id=user_id, created_at=utc_now_iso()))
        return True


def remove_bookmark(set_id: str, user_id: str) -> bool:
    with session_scope() as session:
        deleted = session.query(BookmarkModel).filter(BookmarkModel.set_id == set_id, BookmarkModel.user_id == user_id).delete(synchronize_session=False)
        return deleted > 0


def is_bookmarked(set_id: str, user_id: str) -> bool:
    with session_scope() as session:
        return session.execute(select(BookmarkModel).where(BookmarkModel.set_id == set_id, BookmarkModel.user_id == user_id)).scalars().first() is not None


def get_user_bookmarks(user_id: str) -> List[Dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(BookmarkModel).where(BookmarkModel.user_id == user_id)).scalars().all()

    result = []
    for bookmark in rows:
        set_data = get_set(bookmark.set_id)
        if set_data:
            set_data['bookmarked_at'] = bookmark.created_at
            result.append(set_data)
    return result


def add_comment_like(comment_id: str, user_id: str) -> bool:
    with session_scope() as session:
        exists = session.execute(select(CommentLikeModel).where(CommentLikeModel.comment_id == comment_id, CommentLikeModel.user_id == user_id)).scalars().first()
        if exists:
            return False
        session.add(CommentLikeModel(id=str(uuid.uuid4()), comment_id=comment_id, user_id=user_id, created_at=utc_now_iso()))
        return True


def remove_comment_like(comment_id: str, user_id: str) -> bool:
    with session_scope() as session:
        deleted = session.query(CommentLikeModel).filter(CommentLikeModel.comment_id == comment_id, CommentLikeModel.user_id == user_id).delete(synchronize_session=False)
        return deleted > 0


def get_comment_likes_count(comment_id: str) -> int:
    with session_scope() as session:
        return session.query(CommentLikeModel).filter(CommentLikeModel.comment_id == comment_id).count()


def is_comment_liked(comment_id: str, user_id: str) -> bool:
    with session_scope() as session:
        return session.execute(select(CommentLikeModel).where(CommentLikeModel.comment_id == comment_id, CommentLikeModel.user_id == user_id)).scalars().first() is not None


def add_comment_reply(comment_id: str, user_id: str, username: str, content: str) -> Dict[str, Any]:
    with session_scope() as session:
        row = CommentReplyModel(id=str(uuid.uuid4()), comment_id=comment_id, user_id=user_id, username=username, content=content, created_at=utc_now_iso(), edited_at=None)
        session.add(row)
        session.flush()
        return _comment_reply_dict(row)


def get_comment_replies(comment_id: str) -> List[Dict[str, Any]]:
    with session_scope() as session:
        rows = session.execute(select(CommentReplyModel).where(CommentReplyModel.comment_id == comment_id)).scalars().all()
        rows.sort(key=lambda item: item.created_at or '')
        return [_comment_reply_dict(row) for row in rows]


def get_comment_replies_count(comment_id: str) -> int:
    with session_scope() as session:
        return session.query(CommentReplyModel).filter(CommentReplyModel.comment_id == comment_id).count()


def delete_post(post_id: str, user_id: str) -> bool:
    with session_scope() as session:
        deleted = session.query(PostModel).filter(PostModel.id == post_id, PostModel.user_id == user_id).delete(synchronize_session=False)
        return deleted > 0


def update_post(post_id: str, user_id: str, content: str, image_url: str = None) -> bool:
    with session_scope() as session:
        row = session.execute(select(PostModel).where(PostModel.id == post_id, PostModel.user_id == user_id)).scalars().first()
        if not row:
            return False
        row.content = content
        if image_url is not None:
            row.image_url = image_url
        row.edited_at = utc_now_iso()
        session.add(row)
        return True


def get_post(post_id: str) -> Dict[str, Any]:
    with session_scope() as session:
        row = session.get(PostModel, post_id)
        return _post_dict(row) if row else None


def delete_comment(comment_id: str, user_id: str) -> bool:
    with session_scope() as session:
        row = session.execute(select(CommentModel).where(CommentModel.id == comment_id, CommentModel.user_id == user_id)).scalars().first()
        if not row:
            return False

        reply_ids = [reply[0] for reply in session.execute(select(CommentReplyModel.id).where(CommentReplyModel.comment_id == comment_id)).all()]
        if reply_ids:
            session.query(ReplyLikeModel).filter(ReplyLikeModel.reply_id.in_(reply_ids)).delete(synchronize_session=False)
            session.query(CommentReplyModel).filter(CommentReplyModel.id.in_(reply_ids)).delete(synchronize_session=False)

        session.query(CommentLikeModel).filter(CommentLikeModel.comment_id == comment_id).delete(synchronize_session=False)
        session.query(CommentModel).filter(CommentModel.id == comment_id, CommentModel.user_id == user_id).delete(synchronize_session=False)
        return True


def update_comment(comment_id: str, user_id: str, content: str) -> bool:
    with session_scope() as session:
        row = session.execute(select(CommentModel).where(CommentModel.id == comment_id, CommentModel.user_id == user_id)).scalars().first()
        if not row:
            return False
        row.content = content
        row.edited_at = utc_now_iso()
        session.add(row)
        return True


def delete_comment_replies(comment_id: str) -> bool:
    with session_scope() as session:
        reply_ids = [reply[0] for reply in session.execute(select(CommentReplyModel.id).where(CommentReplyModel.comment_id == comment_id)).all()]
        if not reply_ids:
            return False
        session.query(ReplyLikeModel).filter(ReplyLikeModel.reply_id.in_(reply_ids)).delete(synchronize_session=False)
        deleted = session.query(CommentReplyModel).filter(CommentReplyModel.id.in_(reply_ids)).delete(synchronize_session=False)
        return deleted > 0


def delete_reply(reply_id: str, user_id: str) -> bool:
    with session_scope() as session:
        row = session.execute(select(CommentReplyModel).where(CommentReplyModel.id == reply_id, CommentReplyModel.user_id == user_id)).scalars().first()
        if not row:
            return False
        session.query(ReplyLikeModel).filter(ReplyLikeModel.reply_id == reply_id).delete(synchronize_session=False)
        session.query(CommentReplyModel).filter(CommentReplyModel.id == reply_id, CommentReplyModel.user_id == user_id).delete(synchronize_session=False)
        return True


def update_reply(reply_id: str, user_id: str, content: str) -> bool:
    with session_scope() as session:
        row = session.execute(select(CommentReplyModel).where(CommentReplyModel.id == reply_id, CommentReplyModel.user_id == user_id)).scalars().first()
        if not row:
            return False
        row.content = content
        row.edited_at = utc_now_iso()
        session.add(row)
        return True


def add_reply_like(reply_id: str, user_id: str) -> bool:
    with session_scope() as session:
        exists = session.execute(select(ReplyLikeModel).where(ReplyLikeModel.reply_id == reply_id, ReplyLikeModel.user_id == user_id)).scalars().first()
        if exists:
            return False
        session.add(ReplyLikeModel(id=str(uuid.uuid4()), reply_id=reply_id, user_id=user_id, created_at=utc_now_iso()))
        return True


def remove_reply_like(reply_id: str, user_id: str) -> bool:
    with session_scope() as session:
        deleted = session.query(ReplyLikeModel).filter(ReplyLikeModel.reply_id == reply_id, ReplyLikeModel.user_id == user_id).delete(synchronize_session=False)
        return deleted > 0


def get_reply_likes_count(reply_id: str) -> int:
    with session_scope() as session:
        return session.query(ReplyLikeModel).filter(ReplyLikeModel.reply_id == reply_id).count()


def is_reply_liked(reply_id: str, user_id: str) -> bool:
    with session_scope() as session:
        return session.execute(select(ReplyLikeModel).where(ReplyLikeModel.reply_id == reply_id, ReplyLikeModel.user_id == user_id)).scalars().first() is not None
