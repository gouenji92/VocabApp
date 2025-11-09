import json, uuid, os
from typing import List, Dict, Any
from .schemas import VocabSet, VocabTerm

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SETS_FILE = os.path.join(DATA_DIR, 'sets.json')
TERMS_FILE = os.path.join(DATA_DIR, 'terms.json')

os.makedirs(DATA_DIR, exist_ok=True)

def _load(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        return json.loads(open(path, 'r', encoding='utf-8').read())
    except Exception:
        return []

def _save(path: str, data: List[Dict[str, Any]]):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_sets(user_id: str = None) -> List[Dict[str, Any]]:
    sets = _load(SETS_FILE)
    if user_id:
        return [s for s in sets if s.get('user_id') == user_id]
    return sets

def create_set(name: str, description: str, lang_from: str, lang_to: str, user_id: str = None, visibility: str = 'private', owner_username: str = None) -> Dict[str, Any]:
    from datetime import datetime
    sets = _load(SETS_FILE)
    sid = str(uuid.uuid4())
    row = {
        'id': sid, 
        'name': name, 
        'description': description, 
        'language_from': lang_from, 
        'language_to': lang_to, 
        'user_id': user_id,
        'visibility': visibility,
        'owner_username': owner_username,
        'created_at': datetime.utcnow().isoformat()
    }
    sets.append(row)
    _save(SETS_FILE, sets)
    return row

def list_terms(set_id: str) -> List[Dict[str, Any]]:
    return [t for t in _load(TERMS_FILE) if t.get('set_id') == set_id]

def add_term(set_id: str, term: str, definition: str, pos: str = None, pronunciation: str = None, example: str = None):
    terms = _load(TERMS_FILE)
    row = {'id': str(uuid.uuid4()), 'set_id': set_id, 'term': term, 'definition': definition, 'pos': pos, 'pronunciation': pronunciation, 'example': example}
    terms.append(row)
    _save(TERMS_FILE, terms)
    return row

def get_set(set_id: str) -> Dict[str, Any]:
    sets = _load(SETS_FILE)
    for s in sets:
        if s.get('id') == set_id:
            return s
    return None

def update_set(set_id: str, name: str = None, description: str = None, lang_from: str = None, lang_to: str = None, visibility: str = None) -> Dict[str, Any]:
    """Update an existing vocabulary set"""
    sets = _load(SETS_FILE)
    for i, s in enumerate(sets):
        if s.get('id') == set_id:
            if name is not None:
                s['name'] = name
            if description is not None:
                s['description'] = description
            if lang_from is not None:
                s['language_from'] = lang_from
            if lang_to is not None:
                s['language_to'] = lang_to
            if visibility is not None:
                s['visibility'] = visibility
            sets[i] = s
            _save(SETS_FILE, sets)
            return s
    return None

def delete_set(set_id: str):
    """Delete a vocabulary set and all its terms"""
    # Delete the set
    sets = _load(SETS_FILE)
    sets = [s for s in sets if s.get('id') != set_id]
    _save(SETS_FILE, sets)
    
    # Delete all terms in this set
    terms = _load(TERMS_FILE)
    terms = [t for t in terms if t.get('set_id') != set_id]
    _save(TERMS_FILE, terms)
    
    # Delete all progress for terms in this set
    progs = _load(PROGRESS_FILE)
    term_ids_to_delete = [t['id'] for t in _load(TERMS_FILE) if t.get('set_id') == set_id]
    progs = [p for p in progs if p.get('term_id') not in term_ids_to_delete]
    _save(PROGRESS_FILE, progs)

def delete_term(term_id: str):
    terms = _load(TERMS_FILE)
    terms = [t for t in terms if t.get('id') != term_id]
    _save(TERMS_FILE, terms)
    
    # Also delete progress for this term
    progs = _load(PROGRESS_FILE)
    progs = [p for p in progs if p.get('term_id') != term_id]
    _save(PROGRESS_FILE, progs)

def update_term(term_id: str, term: str = None, definition: str = None, pos: str = None, example: str = None):
    """Update an existing term"""
    terms = _load(TERMS_FILE)
    for i, t in enumerate(terms):
        if t.get('id') == term_id:
            if term is not None:
                t['term'] = term
            if definition is not None:
                t['definition'] = definition
            if pos is not None:
                t['pos'] = pos
            if example is not None:
                t['example'] = example
            terms[i] = t
            _save(TERMS_FILE, terms)
            return t
    return None

def get_term(term_id: str) -> Dict[str, Any]:
    """Get a single term by ID"""
    terms = _load(TERMS_FILE)
    for t in terms:
        if t.get('id') == term_id:
            return t
    return None

# ---- Progress (spaced repetition) ----
PROGRESS_FILE = os.path.join(DATA_DIR, 'progress.json')
LIKES_FILE = os.path.join(DATA_DIR, 'likes.json')
COMMENTS_FILE = os.path.join(DATA_DIR, 'comments.json')
SHARES_FILE = os.path.join(DATA_DIR, 'shares.json')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')
BOOKMARKS_FILE = os.path.join(DATA_DIR, 'bookmarks.json')
COMMENT_LIKES_FILE = os.path.join(DATA_DIR, 'comment_likes.json')
COMMENT_REPLIES_FILE = os.path.join(DATA_DIR, 'comment_replies.json')

def get_progress(term_id: str, user_id: str = 'default') -> Dict[str, Any]:
    progs = _load(PROGRESS_FILE)
    for p in progs:
        if p.get('term_id') == term_id and p.get('user_id') == user_id:
            return p
    return None

def save_progress(term_id: str, easiness: float, repetitions: int, interval: int, next_review: str, user_id: str = 'default'):
    from datetime import datetime
    progs = _load(PROGRESS_FILE)
    existing = None
    for i, p in enumerate(progs):
        if p.get('term_id') == term_id and p.get('user_id') == user_id:
            existing = i
            break
    row = {
        'term_id': term_id,
        'user_id': user_id,
        'easiness': easiness,
        'repetitions': repetitions,
        'interval_days': interval,
        'next_review': next_review,
        'last_review': datetime.utcnow().isoformat()
    }
    if existing is not None:
        progs[existing] = row
    else:
        progs.append(row)
    _save(PROGRESS_FILE, progs)

def list_progress(set_id: str, user_id: str = 'default') -> List[Dict[str, Any]]:
    terms = list_terms(set_id)
    term_ids = [t['id'] for t in terms]
    progs = _load(PROGRESS_FILE)
    return [p for p in progs if p.get('term_id') in term_ids and p.get('user_id') == user_id]

def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get statistics for a user"""
    from datetime import datetime, date
    
    # Get all user's sets
    sets = list_sets(user_id)
    
    # Get all terms from user's sets
    all_terms = []
    for s in sets:
        all_terms.extend(list_terms(s['id']))
    
    # Get all progress for user
    progs = _load(PROGRESS_FILE)
    user_progs = [p for p in progs if p.get('user_id') == user_id]
    
    # Calculate stats
    total_words = len(all_terms)
    learned_words = len([p for p in user_progs if p.get('repetitions', 0) > 0])
    
    # Words due today
    today = date.today().isoformat()
    due_today = len([p for p in user_progs if p.get('next_review', '') <= today])
    
    # Calculate accuracy (based on easiness factor > 2.5 means good)
    if user_progs:
        avg_easiness = sum(p.get('easiness', 2.5) for p in user_progs) / len(user_progs)
        accuracy = min(100, max(0, (avg_easiness - 1.3) / (4.0 - 1.3) * 100))
    else:
        accuracy = 0
    
    # Study streak (consecutive days with reviews)
    review_dates = []
    for p in user_progs:
        last_review = p.get('last_review')
        if last_review:
            try:
                review_date = datetime.fromisoformat(last_review).date()
                review_dates.append(review_date)
            except:
                pass
    
    streak = 0
    if review_dates:
        review_dates = sorted(set(review_dates), reverse=True)
        current_date = date.today()
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
        'streak': streak
    }

# ---- Sharing & Community ----
def list_public_sets(search: str = None, language_from: str = None, language_to: str = None) -> List[Dict[str, Any]]:
    """Get all public sets with optional filters"""
    sets = _load(SETS_FILE)
    public_sets = [s for s in sets if s.get('visibility') == 'public']
    
    # Apply filters
    if search:
        search_lower = search.lower()
        public_sets = [s for s in public_sets if 
                      search_lower in s.get('name', '').lower() or 
                      search_lower in s.get('description', '').lower()]
    
    if language_from:
        public_sets = [s for s in public_sets if s.get('language_from') == language_from]
    
    if language_to:
        public_sets = [s for s in public_sets if s.get('language_to') == language_to]
    
    # Add term count to each set
    for s in public_sets:
        s['term_count'] = len(list_terms(s['id']))
    
    return public_sets

def clone_set(set_id: str, new_user_id: str, new_username: str = None) -> Dict[str, Any]:
    """Clone a public set to a user's collection"""
    original_set = get_set(set_id)
    if not original_set or original_set.get('visibility') != 'public':
        return None
    
    # Create new set for user
    new_set = create_set(
        name=f"{original_set['name']} (Copy)",
        description=f"Copied from {original_set.get('owner_username', 'Unknown')}. {original_set.get('description', '')}",
        lang_from=original_set['language_from'],
        lang_to=original_set['language_to'],
        user_id=new_user_id,
        visibility='private',
        owner_username=new_username
    )
    
    # Copy all terms
    original_terms = list_terms(set_id)
    for term in original_terms:
        add_term(
            set_id=new_set['id'],
            term=term['term'],
            definition=term['definition'],
            pos=term.get('pos'),
            example=term.get('example')
        )
    
    return new_set


# ---- Social Features: Likes, Comments, Shares ----
def add_like(set_id: str, user_id: str):
    """Thêm like cho bộ từ"""
    likes = _load(LIKES_FILE)
    # Check if already liked
    for like in likes:
        if like.get('set_id') == set_id and like.get('user_id') == user_id:
            return False  # Already liked
    
    from datetime import datetime
    likes.append({
        'id': str(uuid.uuid4()),
        'set_id': set_id,
        'user_id': user_id,
        'created_at': datetime.utcnow().isoformat()
    })
    _save(LIKES_FILE, likes)
    return True

def remove_like(set_id: str, user_id: str):
    """Bỏ like cho bộ từ"""
    likes = _load(LIKES_FILE)
    likes = [l for l in likes if not (l.get('set_id') == set_id and l.get('user_id') == user_id)]
    _save(LIKES_FILE, likes)
    return True

def get_likes_count(set_id: str) -> int:
    """Đếm số lượt like"""
    likes = _load(LIKES_FILE)
    return len([l for l in likes if l.get('set_id') == set_id])

def is_liked_by_user(set_id: str, user_id: str) -> bool:
    """Kiểm tra user đã like chưa"""
    likes = _load(LIKES_FILE)
    return any(l.get('set_id') == set_id and l.get('user_id') == user_id for l in likes)

def add_comment(set_id: str, user_id: str, username: str, content: str) -> Dict[str, Any]:
    """Thêm bình luận cho bộ từ"""
    from datetime import datetime
    comments = _load(COMMENTS_FILE)
    comment = {
        'id': str(uuid.uuid4()),
        'set_id': set_id,
        'user_id': user_id,
        'username': username,
        'content': content,
        'created_at': datetime.utcnow().isoformat()
    }
    comments.append(comment)
    _save(COMMENTS_FILE, comments)
    return comment

def get_comments(set_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách bình luận"""
    comments = _load(COMMENTS_FILE)
    set_comments = [c for c in comments if c.get('set_id') == set_id]
    # Sort by created_at descending
    set_comments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return set_comments

def get_comments_count(set_id: str) -> int:
    """Đếm số bình luận"""
    comments = _load(COMMENTS_FILE)
    return len([c for c in comments if c.get('set_id') == set_id])

def add_share(set_id: str, user_id: str):
    """Ghi nhận lượt share"""
    from datetime import datetime
    shares = _load(SHARES_FILE)
    shares.append({
        'id': str(uuid.uuid4()),
        'set_id': set_id,
        'user_id': user_id,
        'created_at': datetime.utcnow().isoformat()
    })
    _save(SHARES_FILE, shares)
    return True

def get_shares_count(set_id: str) -> int:
    """Đếm số lượt share"""
    shares = _load(SHARES_FILE)
    return len([s for s in shares if s.get('set_id') == set_id])

def get_feed_posts(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Lấy danh sách posts cho feed (các bộ từ công khai, sắp xếp theo thời gian)"""
    sets = _load(SETS_FILE)
    public_sets = [s for s in sets if s.get('visibility') == 'public']
    
    # Sort by created_at descending (newest first)
    public_sets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Add social stats and preview terms
    for s in public_sets:
        s['likes_count'] = get_likes_count(s['id'])
        s['comments_count'] = get_comments_count(s['id'])
        s['shares_count'] = get_shares_count(s['id'])
        
        # Get first 3 terms for preview
        terms = list_terms(s['id'])
        s['term_count'] = len(terms)
        s['preview_terms'] = terms[:3] if len(terms) > 3 else terms
        s['post_type'] = 'vocab_set'  # Type marker
    
    # Pagination
    return public_sets[offset:offset + limit]


# ---- Posts (Bài viết text thuần) ----
def create_post(user_id: str, username: str, content: str, attached_set_id: str = None, image_url: str = None) -> Dict[str, Any]:
    """Tạo bài viết mới lên feed"""
    from datetime import datetime
    posts = _load(POSTS_FILE)
    
    post = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'username': username,
        'content': content,
        'attached_set_id': attached_set_id,
        'image_url': image_url,
        'created_at': datetime.utcnow().isoformat(),
        'post_type': 'text_post'
    }
    
    posts.append(post)
    _save(POSTS_FILE, posts)
    return post

def list_all_feed_items(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Lấy tất cả feed items (posts + public sets) và merge lại"""
    from .auth import get_user
    
    # Get text posts
    posts = _load(POSTS_FILE)
    for p in posts:
        p['post_type'] = 'text_post'
        p['likes_count'] = get_likes_count(p['id'])
        p['comments_count'] = get_comments_count(p['id'])
        p['shares_count'] = get_shares_count(p['id'])
        
        # Get user info (avatar, display_name)
        user_info = get_user(p.get('username') or p.get('user_id'))
        if user_info:
            p['user_avatar'] = user_info.get('avatar')
            p['user_display_name'] = user_info.get('display_name') or p.get('username')
        
        # If has attached set, get set info
        if p.get('attached_set_id'):
            attached_set = get_set(p['attached_set_id'])
            if attached_set:
                terms = list_terms(attached_set['id'])
                p['attached_set'] = attached_set
                p['attached_set']['term_count'] = len(terms)
                p['attached_set']['preview_terms'] = terms[:3] if len(terms) > 3 else terms
    
    # Get public vocab sets (treated as posts)
    sets = _load(SETS_FILE)
    public_sets = [s for s in sets if s.get('visibility') == 'public']
    
    for s in public_sets:
        s['post_type'] = 'vocab_set'
        s['likes_count'] = get_likes_count(s['id'])
        s['comments_count'] = get_comments_count(s['id'])
        s['shares_count'] = get_shares_count(s['id'])
        
        # Get preview terms
        terms = list_terms(s['id'])
        s['term_count'] = len(terms)
        s['preview_terms'] = terms[:3] if len(terms) > 3 else terms
        
        # For consistency with text posts
        s['content'] = s.get('description', '')
        s['username'] = s.get('owner_username', 'Unknown')
        
        # Get user info (avatar, display_name)
        user_info = get_user(s.get('owner_username') or s.get('user_id'))
        if user_info:
            s['user_avatar'] = user_info.get('avatar')
            s['user_display_name'] = user_info.get('display_name') or s.get('username')
    
    # Merge and sort by created_at
    all_items = posts + public_sets
    all_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Pagination
    return all_items[offset:offset + limit]

def get_user_posts(username: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Lấy bài viết của một user cụ thể (chỉ text posts, không bao gồm vocab sets)"""
    posts = _load(POSTS_FILE)
    user_posts = [p for p in posts if p.get('username') == username or p.get('user_id') == username]
    
    # Add stats and attached set info
    for p in user_posts:
        p['post_type'] = 'text_post'
        p['likes_count'] = get_likes_count(p['id'])
        p['comments_count'] = get_comments_count(p['id'])
        p['shares_count'] = get_shares_count(p['id'])
        
        # If has attached set, get set info
        if p.get('attached_set_id'):
            attached_set = get_set(p['attached_set_id'])
            if attached_set:
                terms = list_terms(attached_set['id'])
                p['attached_set'] = attached_set
                p['attached_set']['term_count'] = len(terms)
                p['attached_set']['preview_terms'] = terms[:3] if len(terms) > 3 else terms
    
    # Sort by created_at
    user_posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Pagination
    return user_posts[offset:offset + limit]


# ---- Bookmarks (Lưu bộ từ) ----
def add_bookmark(set_id: str, user_id: str) -> bool:
    """Lưu bộ từ vào danh sách bookmark"""
    from datetime import datetime
    bookmarks = _load(BOOKMARKS_FILE)
    
    # Check if already bookmarked
    if any(b.get('set_id') == set_id and b.get('user_id') == user_id for b in bookmarks):
        return False
    
    bookmarks.append({
        'id': str(uuid.uuid4()),
        'set_id': set_id,
        'user_id': user_id,
        'created_at': datetime.utcnow().isoformat()
    })
    _save(BOOKMARKS_FILE, bookmarks)
    return True

def remove_bookmark(set_id: str, user_id: str) -> bool:
    """Xóa bookmark"""
    bookmarks = _load(BOOKMARKS_FILE)
    filtered = [b for b in bookmarks if not (b.get('set_id') == set_id and b.get('user_id') == user_id)]
    if len(filtered) < len(bookmarks):
        _save(BOOKMARKS_FILE, filtered)
        return True
    return False

def is_bookmarked(set_id: str, user_id: str) -> bool:
    """Kiểm tra xem user đã bookmark bộ từ chưa"""
    bookmarks = _load(BOOKMARKS_FILE)
    return any(b.get('set_id') == set_id and b.get('user_id') == user_id for b in bookmarks)

def get_user_bookmarks(user_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách bookmarks của user"""
    bookmarks = _load(BOOKMARKS_FILE)
    user_bookmarks = [b for b in bookmarks if b.get('user_id') == user_id]
    
    # Get full set info for each bookmark
    result = []
    for bm in user_bookmarks:
        set_data = get_set(bm['set_id'])
        if set_data:
            set_data['bookmarked_at'] = bm.get('created_at')
            result.append(set_data)
    
    return result


# ---- Comment Likes ----
def add_comment_like(comment_id: str, user_id: str) -> bool:
    """Thích một bình luận"""
    from datetime import datetime
    likes = _load(COMMENT_LIKES_FILE)
    
    # Check if already liked
    if any(l.get('comment_id') == comment_id and l.get('user_id') == user_id for l in likes):
        return False
    
    likes.append({
        'id': str(uuid.uuid4()),
        'comment_id': comment_id,
        'user_id': user_id,
        'created_at': datetime.utcnow().isoformat()
    })
    _save(COMMENT_LIKES_FILE, likes)
    return True

def remove_comment_like(comment_id: str, user_id: str) -> bool:
    """Bỏ thích bình luận"""
    likes = _load(COMMENT_LIKES_FILE)
    filtered = [l for l in likes if not (l.get('comment_id') == comment_id and l.get('user_id') == user_id)]
    if len(filtered) < len(likes):
        _save(COMMENT_LIKES_FILE, filtered)
        return True
    return False

def get_comment_likes_count(comment_id: str) -> int:
    """Đếm số lượt thích của bình luận"""
    likes = _load(COMMENT_LIKES_FILE)
    return len([l for l in likes if l.get('comment_id') == comment_id])

def is_comment_liked(comment_id: str, user_id: str) -> bool:
    """Kiểm tra user đã thích comment chưa"""
    likes = _load(COMMENT_LIKES_FILE)
    return any(l.get('comment_id') == comment_id and l.get('user_id') == user_id for l in likes)


# ---- Comment Replies ----
def add_comment_reply(comment_id: str, user_id: str, username: str, content: str) -> Dict[str, Any]:
    """Trả lời một bình luận"""
    from datetime import datetime
    replies = _load(COMMENT_REPLIES_FILE)
    reply = {
        'id': str(uuid.uuid4()),
        'comment_id': comment_id,
        'user_id': user_id,
        'username': username,
        'content': content,
        'created_at': datetime.utcnow().isoformat()
    }
    replies.append(reply)
    _save(COMMENT_REPLIES_FILE, replies)
    return reply

def get_comment_replies(comment_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách trả lời của một comment"""
    replies = _load(COMMENT_REPLIES_FILE)
    comment_replies = [r for r in replies if r.get('comment_id') == comment_id]
    comment_replies.sort(key=lambda x: x.get('created_at', ''))
    return comment_replies

def get_comment_replies_count(comment_id: str) -> int:
    """Đếm số lượng reply của comment"""
    replies = _load(COMMENT_REPLIES_FILE)
    return len([r for r in replies if r.get('comment_id') == comment_id])


# ---- Post Management: Delete & Edit ----
def delete_post(post_id: str, user_id: str) -> bool:
    """Xóa bài viết (chỉ người tạo mới được xóa)"""
    posts = _load(POSTS_FILE)
    for i, post in enumerate(posts):
        if post.get('id') == post_id and post.get('user_id') == user_id:
            posts.pop(i)
            _save(POSTS_FILE, posts)
            return True
    return False

def update_post(post_id: str, user_id: str, content: str, image_url: str = None) -> bool:
    """Chỉnh sửa nội dung bài viết (chỉ người tạo)"""
    from datetime import datetime
    posts = _load(POSTS_FILE)
    for post in posts:
        if post.get('id') == post_id and post.get('user_id') == user_id:
            post['content'] = content
            if image_url is not None:
                post['image_url'] = image_url
            post['edited_at'] = datetime.utcnow().isoformat()
            _save(POSTS_FILE, posts)
            return True
    return False

def get_post(post_id: str) -> Dict[str, Any]:
    """Lấy thông tin một bài viết"""
    posts = _load(POSTS_FILE)
    for post in posts:
        if post.get('id') == post_id:
            return post
    return None


# ---- Comment Management: Delete & Edit ----
def delete_comment(comment_id: str, user_id: str) -> bool:
    """Xóa comment (chỉ người tạo mới được xóa)"""
    comments = _load(COMMENTS_FILE)
    for i, comment in enumerate(comments):
        if comment.get('id') == comment_id and comment.get('user_id') == user_id:
            comments.pop(i)
            _save(COMMENTS_FILE, comments)
            # Xóa luôn các replies của comment này
            delete_comment_replies(comment_id)
            return True
    return False

def update_comment(comment_id: str, user_id: str, content: str) -> bool:
    """Chỉnh sửa nội dung comment (chỉ người tạo)"""
    from datetime import datetime
    comments = _load(COMMENTS_FILE)
    for comment in comments:
        if comment.get('id') == comment_id and comment.get('user_id') == user_id:
            comment['content'] = content
            comment['edited_at'] = datetime.utcnow().isoformat()
            _save(COMMENTS_FILE, comments)
            return True
    return False

def delete_comment_replies(comment_id: str) -> bool:
    """Xóa tất cả replies của một comment"""
    replies = _load(COMMENT_REPLIES_FILE)
    original_count = len(replies)
    replies = [r for r in replies if r.get('comment_id') != comment_id]
    _save(COMMENT_REPLIES_FILE, replies)
    return len(replies) < original_count


# ---- Reply Management: Delete & Edit ----
def delete_reply(reply_id: str, user_id: str) -> bool:
    """Xóa reply (chỉ người tạo mới được xóa)"""
    replies = _load(COMMENT_REPLIES_FILE)
    for i, reply in enumerate(replies):
        if reply.get('id') == reply_id and reply.get('user_id') == user_id:
            replies.pop(i)
            _save(COMMENT_REPLIES_FILE, replies)
            return True
    return False

def update_reply(reply_id: str, user_id: str, content: str) -> bool:
    """Chỉnh sửa nội dung reply (chỉ người tạo)"""
    from datetime import datetime
    replies = _load(COMMENT_REPLIES_FILE)
    for reply in replies:
        if reply.get('id') == reply_id and reply.get('user_id') == user_id:
            reply['content'] = content
            reply['edited_at'] = datetime.utcnow().isoformat()
            _save(COMMENT_REPLIES_FILE, replies)
            return True
    return False


