from fastapi import FastAPI, UploadFile, File, Form, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
import os
import io
import csv
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .detect import read_any, choose_mapping
from .storage import (
    create_set, add_term, list_sets, get_set, list_terms, delete_term,
    get_progress, save_progress, list_progress, update_set, delete_set,
    update_term, get_term, get_user_stats, list_public_sets, clone_set,
    add_like, remove_like, get_likes_count, is_liked_by_user,
    add_comment, get_comments, get_comments_count, add_share, get_shares_count,
    get_feed_posts, create_post, list_all_feed_items, get_user_posts,
    add_bookmark, remove_bookmark, is_bookmarked, get_user_bookmarks,
    add_comment_like, remove_comment_like, get_comment_likes_count, is_comment_liked,
    add_comment_reply, get_comment_replies, get_comment_replies_count,
    delete_post, update_post, get_post,
    delete_comment, update_comment,
    delete_reply, update_reply
)
from .auth import create_user, verify_user, get_user
from .auth import update_user_profile, change_user_password
from .auth import follow_user, unfollow_user, is_following, get_followers, get_following
from . import ai_helper
from .oauth import oauth

app = FastAPI(title='Vocab App (VN)')

base_dir = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(base_dir, 'templates'))

# Mount static assets (CSS, JS, images)
static_dir = os.path.join(base_dir, 'static')
if os.path.isdir(static_dir):
    app.mount('/static', StaticFiles(directory=static_dir), name='static')
else:
    # Optional: log warning to console; avoids startup crash if missing
    print('[WARN] Static directory not found:', static_dir)
    os.makedirs(static_dir, exist_ok=True)

# Ensure avatars directory exists inside static
avatars_dir = os.path.join(static_dir, 'avatars')
os.makedirs(avatars_dir, exist_ok=True)

# Ensure uploads directory exists for post images
uploads_dir = os.path.join(static_dir, 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

# Session management
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
# Use a distinct cookie name for Starlette's session to avoid clashing with our auth 'session' cookie
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie='framework_session')
serializer = URLSafeTimedSerializer(SECRET_KEY)
# (Using single 'session' cookie for auth)

# Simple request logger to debug routing issues (OAuth redirects, etc.)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        print(f"REQ {request.method} {request.url.path}")
    except Exception:
        pass
    response = await call_next(request)
    return response

def create_session_token(username: str) -> str:
    return serializer.dumps(username, salt='session')

def verify_session_token(token: str) -> Optional[str]:
    try:
        username = serializer.loads(token, salt='session', max_age=7*24*60*60)  # 7 days
        return username
    except Exception:
        return None

def get_current_user(session: Optional[str] = Cookie(None)) -> Optional[str]:
    if not session:
        return None
    return verify_session_token(session)


# -------------------- Auth Routes --------------------
@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse('login.html', { 'request': request, 'error': None })


@app.post('/login')
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = verify_user(username, password)
    if not user:
        return templates.TemplateResponse('login.html', { 'request': request, 'error': 'Tên đăng nhập hoặc mật khẩu không đúng' })
    
    token = create_session_token(username)
    response = RedirectResponse(url='/feed', status_code=303)
    response.set_cookie(key='session', value=token, httponly=True, max_age=7*24*60*60)
    return response


@app.get('/register', response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse('register.html', { 'request': request, 'error': None })


@app.post('/register')
def register(request: Request, username: str = Form(...), password: str = Form(...), password2: str = Form(...), email: str = Form(None)):
    if password != password2:
        return templates.TemplateResponse('register.html', { 'request': request, 'error': 'Mật khẩu không khớp' })
    
    try:
        create_user(username, password, email)
    except ValueError as e:
        return templates.TemplateResponse('register.html', { 'request': request, 'error': str(e) })
    
    # Auto login after register
    token = create_session_token(username)
    response = RedirectResponse(url='/feed', status_code=303)
    response.set_cookie(key='session', value=token, httponly=True, max_age=7*24*60*60)
    return response


@app.get('/logout')
def logout():
    response = RedirectResponse(url='/login', status_code=303)
    response.delete_cookie(key='session')
    return response


# -------------------- Dashboard --------------------


@app.get('/dashboard', response_class=HTMLResponse)
def dashboard_page(request: Request, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    stats = get_user_stats(username)
    recent_sets = list_sets(user_id=username)[:5]  # Get 5 most recent sets
    user_obj = get_user(username)
    
    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'username': username,
        'user': user_obj,
        'stats': stats,
        'recent_sets': recent_sets
    })


# -------------------- Upload Routes --------------------


@app.get('/', response_class=HTMLResponse)
def home(request: Request, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    return RedirectResponse(url='/feed', status_code=303)


@app.post('/preview')
async def preview(file: UploadFile = File(...), set_name: str = Form(...), language_from: str = Form('en'), language_to: str = Form('vi')):
    rows = await read_any(file)
    mapping, headers = choose_mapping(rows)
    sample = rows[:5]
    return {
        'mapping': mapping,
        'headers': headers,
        'sample': sample,
        'set_name': set_name,
        'language_from': language_from,
        'language_to': language_to,
    }


@app.post('/import')
async def import_data(
    session: Optional[str] = Cookie(None),
    file: UploadFile = File(...),
    set_id: Optional[str] = Form(None),
    set_name: Optional[str] = Form(None),
    language_from: str = Form('en'),
    language_to: str = Form('vi'),
    word_col: Optional[str] = Form(None),
    pos_col: Optional[str] = Form(None),
    pronunciation_col: Optional[str] = Form(None),
    example_col: Optional[str] = Form(None),
    meaning_col: Optional[str] = Form(None),
    visibility: str = Form('private'),
):
    username = get_current_user(session)
    if not username:
        return { 'error': 'Vui lòng đăng nhập' }
    rows = await read_any(file)
    auto_map, _ = choose_mapping(rows)
    word = word_col or auto_map.get('word')
    meaning = meaning_col or auto_map.get('meaning')
    pos = pos_col or auto_map.get('pos')
    pronunciation = pronunciation_col or auto_map.get('pronunciation')
    example = example_col or auto_map.get('example')
    if not word or not meaning:
        return { 'error': 'Không xác định được cột từ/ nghĩa' }

    sid = set_id
    if not sid:
        # create set locally with user_id
        new_set = create_set(set_name or 'Bộ từ', f'Import from {file.filename}', language_from, language_to, username, 'private', username)
        sid = new_set['id']

    inserted = 0
    skipped = 0
    for r in rows:
        term_val = (r.get(word) or '').strip()
        meaning_val = (r.get(meaning) or '').strip()
        pos_val = (r.get(pos) or '').strip() if pos else None
        pronunciation_val = (r.get(pronunciation) or '').strip() if pronunciation else None
        example_val = (r.get(example) or '').strip() if example else None
        if not term_val or not meaning_val:
            skipped += 1
            continue
        add_term(sid, term_val, meaning_val, pos_val, pronunciation_val, example_val)
        inserted += 1

    return { 'set_id': sid, 'inserted': inserted, 'skipped': skipped }


@app.get('/sets/create', response_class=HTMLResponse)
def create_set_page(request: Request, session: Optional[str] = Cookie(None)):
    """Render page to create new vocabulary set manually"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    user_obj = get_user(username)
    return templates.TemplateResponse('create_set.html', { 'request': request, 'username': username, 'user': user_obj })


@app.post('/sets/create')
async def create_set_submit(request: Request, session: Optional[str] = Cookie(None)):
    """Handle form submission to create new set with terms"""
    username = get_current_user(session)
    if not username:
        return { 'error': 'Vui lòng đăng nhập' }
    
    form_data = await request.form()
    set_name = form_data.get('set_name', '').strip()
    description = form_data.get('description', '').strip()
    language_from = form_data.get('language_from', 'en').strip()
    language_to = form_data.get('language_to', 'vi').strip()
    visibility = form_data.get('visibility', 'private')
    
    if not set_name:
        return { 'error': 'Tên bộ từ không được để trống' }
    
    # Create the set
    new_set = create_set(set_name, description, language_from, language_to, username, visibility, username)
    set_id = new_set['id']
    
    # Extract terms from form data
    # Form sends: terms[1][term], terms[1][definition], terms[1][pos], etc.
    terms_dict = {}
    for key, value in form_data.items():
        if key.startswith('terms['):
            # Parse: terms[1][term] -> (1, 'term')
            parts = key.replace('terms[', '').replace(']', '|').split('|')
            if len(parts) >= 2:
                term_id = parts[0]
                field_name = parts[1]
                if term_id not in terms_dict:
                    terms_dict[term_id] = {}
                terms_dict[term_id][field_name] = value.strip() if isinstance(value, str) else ''
    
    # Add terms to the set
    inserted = 0
    for term_id, term_data in terms_dict.items():
        term_val = term_data.get('term', '').strip()
        definition_val = term_data.get('definition', '').strip()
        pos_val = term_data.get('pos', '').strip() or None
        pronunciation_val = term_data.get('pronunciation', '').strip() or None
        example_val = term_data.get('example', '').strip() or None
        
        if term_val and definition_val:
            add_term(set_id, term_val, definition_val, pos_val, pronunciation_val, example_val)
            inserted += 1
    
    return { 'set_id': set_id, 'inserted': inserted, 'message': 'Tạo bộ từ thành công!' }


@app.get('/sets', response_class=HTMLResponse)
def sets_page(request: Request, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    sets = list_sets(user_id=username)
    user_obj = get_user(username)
    return templates.TemplateResponse('sets_list.html', { 'request': request, 'sets': sets, 'username': username, 'user': user_obj })


@app.get('/sets/{set_id}', response_class=HTMLResponse)
def set_detail_page(set_id: str, request: Request, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    vset = get_set(set_id)
    if not vset:
        return HTMLResponse('Set not found', status_code=404)
    # Check ownership
    if vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    terms = list_terms(set_id)
    user_obj = get_user(username)
    return templates.TemplateResponse('set_detail.html', { 'request': request, 'vset': vset, 'terms': terms, 'username': username, 'user': user_obj })


@app.get('/sets/{set_id}/export')
def export_set(set_id: str, session: Optional[str] = Cookie(None), format: str = 'csv'):
    """Export vocabulary set to CSV or XLSX"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    vset = get_set(set_id)
    if not vset or vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    
    terms = list_terms(set_id)
    
    if format == 'csv':
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Word', 'Part of Speech', 'Meaning', 'Example'])
        for t in terms:
            writer.writerow([
                t.get('term', ''),
                t.get('pos', ''),
                t.get('definition', ''),
                t.get('example', '')
            ])
        
        output.seek(0)
        filename = f"{vset['name'].replace(' ', '_')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    elif format == 'xlsx':
        # Create XLSX using openpyxl
        try:
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Vocabulary"
            
            # Headers
            ws.append(['Word', 'Part of Speech', 'Meaning', 'Example'])
            
            # Data
            for t in terms:
                ws.append([
                    t.get('term', ''),
                    t.get('pos', ''),
                    t.get('definition', ''),
                    t.get('example', '')
                ])
            
            # Save to BytesIO
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            filename = f"{vset['name'].replace(' ', '_')}.xlsx"
            
            return StreamingResponse(
                output,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except ImportError:
            return HTMLResponse('XLSX export requires openpyxl library', status_code=500)
    
    return HTMLResponse('Invalid format', status_code=400)


@app.get('/sets/{set_id}/edit', response_class=HTMLResponse)
def edit_set_page(set_id: str, request: Request, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    vset = get_set(set_id)
    if not vset:
        return HTMLResponse('Set not found', status_code=404)
    if vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    user_obj = get_user(username)
    return templates.TemplateResponse('set_edit.html', { 'request': request, 'vset': vset, 'username': username, 'user': user_obj })


@app.post('/sets/{set_id}/edit')
def update_set_route(
    set_id: str,
    session: Optional[str] = Cookie(None),
    name: str = Form(...),
    description: str = Form(''),
    language_from: str = Form(...),
    language_to: str = Form(...)
):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    vset = get_set(set_id)
    if not vset or vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    
    update_set(set_id, name, description, language_from, language_to)
    return RedirectResponse(url=f'/sets/{set_id}', status_code=303)


@app.post('/sets/{set_id}/delete')
def delete_set_route(set_id: str, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    vset = get_set(set_id)
    if not vset or vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    
    delete_set(set_id)
    return RedirectResponse(url='/sets', status_code=303)


@app.post('/terms/{term_id}/delete')
def delete_term_route(term_id: str, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    term = get_term(term_id)
    if not term:
        return HTMLResponse('Term not found', status_code=404)
    
    # Check if user owns the set containing this term
    vset = get_set(term['set_id'])
    if not vset or vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    
    delete_term(term_id)
    return RedirectResponse(url=f'/sets/{term["set_id"]}', status_code=303)


@app.get('/terms/{term_id}/edit', response_class=HTMLResponse)
def edit_term_page(term_id: str, request: Request, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    term = get_term(term_id)
    if not term:
        return HTMLResponse('Term not found', status_code=404)
    
    vset = get_set(term['set_id'])
    if not vset or vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    
    user_obj = get_user(username)
    return templates.TemplateResponse('term_edit.html', { 'request': request, 'term': term, 'vset': vset, 'username': username, 'user': user_obj })


@app.post('/terms/{term_id}/edit')
def update_term_route(
    term_id: str,
    session: Optional[str] = Cookie(None),
    term: str = Form(...),
    definition: str = Form(...),
    pos: str = Form(None),
    example: str = Form(None)
):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    term_obj = get_term(term_id)
    if not term_obj:
        return HTMLResponse('Term not found', status_code=404)
    
    vset = get_set(term_obj['set_id'])
    if not vset or vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    
    update_term(term_id, term, definition, pos, example)
    return RedirectResponse(url=f'/sets/{term_obj["set_id"]}', status_code=303)


@app.post('/sets/{set_id}/add-term')
def add_term_route(
    set_id: str,
    session: Optional[str] = Cookie(None),
    term: str = Form(...),
    definition: str = Form(...),
    pos: str = Form(None),
    example: str = Form(None)
):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    vset = get_set(set_id)
    if not vset or vset.get('user_id') != username:
        return HTMLResponse('Unauthorized', status_code=403)
    
    add_term(set_id, term, definition, pos, example)
    return RedirectResponse(url=f'/sets/{set_id}', status_code=303)


@app.get('/study/{set_id}', response_class=HTMLResponse)
def study_page(set_id: str, request: Request, mode: str = 'flashcard', session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    vset = get_set(set_id)
    if not vset:
        return HTMLResponse('Set not found', status_code=404)
    
    user_obj = get_user(username)
    
    # If no mode or want to choose, show mode selection
    if not mode or mode == 'select':
        return templates.TemplateResponse('study_mode.html', { 'request': request, 'set_id': set_id, 'set_name': vset['name'], 'username': username, 'user': user_obj })
    
    # Route to appropriate study template
    if mode == 'flashcard':
        template = 'study.html'
    elif mode == 'fill':
        template = 'study_fill.html'
    elif mode == 'choice':
        template = 'study_choice.html'
    else:
        template = 'study.html'
    
    return templates.TemplateResponse(template, { 'request': request, 'set_id': set_id, 'set_name': vset['name'], 'mode': mode, 'username': username, 'user': user_obj })


# ---- Spaced Repetition API ----
DEFAULT_EASINESS = 2.5

def sm2_update(easiness: float, repetitions: int, interval: int, quality: int):
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * easiness)
        repetitions += 1
    easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if easiness < 1.3:
        easiness = 1.3
    return easiness, repetitions, interval


@app.post('/api/next')
def next_term(req: dict, session: Optional[str] = Cookie(None)):
    username = get_current_user(session) or 'anonymous'
    set_id = req.get('set_id')
    user_id = username
    terms = list_terms(set_id)
    if not terms:
        return {'term': None}
    progs = list_progress(set_id, user_id)
    prog_map = {p['term_id']: p for p in progs}
    now = datetime.utcnow().date().isoformat()
    due = []
    unseen = []
    future = []
    for t in terms:
        p = prog_map.get(t['id'])
        if not p:
            unseen.append(t)
        else:
            nr = p.get('next_review')
            if nr and nr <= now:
                due.append((nr, t))
            else:
                future.append((nr, t))
    if due:
        due.sort(key=lambda x: x[0])
        chosen = due[0][1]
    elif unseen:
        chosen = unseen[0]
    else:
        future.sort(key=lambda x: x[0])
        chosen = future[0][1] if future else None
    return {'term': chosen}


@app.post('/api/answer')
def answer_term(req: dict, session: Optional[str] = Cookie(None)):
    username = get_current_user(session) or 'anonymous'
    term_id = req.get('term_id')
    rating = req.get('rating', 0)
    user_id = username
    if rating < 0 or rating > 5:
        return {'error': 'rating must be 0-5'}
    p = get_progress(term_id, user_id)
    if p:
        easiness = p.get('easiness', DEFAULT_EASINESS)
        repetitions = p.get('repetitions', 0)
        interval = p.get('interval_days', 1)
    else:
        easiness = DEFAULT_EASINESS
        repetitions = 0
        interval = 1
    easiness, repetitions, interval = sm2_update(easiness, repetitions, interval, rating)
    next_review = (datetime.utcnow() + timedelta(days=interval)).date().isoformat()
    save_progress(term_id, easiness, repetitions, interval, next_review, user_id)
    return {'status': 'ok', 'next_review': next_review, 'interval': interval}


@app.post('/api/choice')
def get_choice_question(req: dict, session: Optional[str] = Cookie(None)):
    """Generate multiple choice question with distractors"""
    username = get_current_user(session) or 'anonymous'
    set_id = req.get('set_id')
    user_id = username
    
    # Get next term
    terms = list_terms(set_id)
    if not terms:
        return {'term': None}
    
    progs = list_progress(set_id, user_id)
    prog_map = {p['term_id']: p for p in progs}
    now = datetime.utcnow().date().isoformat()
    due = []
    unseen = []
    future = []
    for t in terms:
        p = prog_map.get(t['id'])
        if not p:
            unseen.append(t)
        else:
            nr = p.get('next_review')
            if nr and nr <= now:
                due.append((nr, t))
            else:
                future.append((nr, t))
    if due:
        due.sort(key=lambda x: x[0])
        chosen = due[0][1]
    elif unseen:
        chosen = unseen[0]
    else:
        future.sort(key=lambda x: x[0])
        chosen = future[0][1] if future else None
    
    if not chosen:
        return {'term': None}
    
    # Generate distractors
    import random
    other_terms = [t for t in terms if t['id'] != chosen['id']]
    distractors = random.sample(other_terms, min(3, len(other_terms)))
    
    choices = [chosen] + distractors
    random.shuffle(choices)
    
    return {
        'term': chosen,
        'choices': [{'id': c['id'], 'definition': c['definition']} for c in choices]
    }

# ============ AI Routes ============

@app.post('/api/ai/translate')
async def api_translate(request: Request, session: Optional[str] = Cookie(None)):
    """Translate text using AI"""
    username = verify_session_token(session) if session else None
    if not username:
        return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    text = data.get('text', '').strip()
    from_lang = data.get('from_lang', 'en')
    to_lang = data.get('to_lang', 'vi')
    
    if not text:
        return JSONResponse({'success': False, 'error': 'Text is required'})
    
    result = await ai_helper.translate_text(text, from_lang, to_lang)
    return JSONResponse(result)

@app.post('/api/ai/grammar')
async def api_grammar(request: Request, session: Optional[str] = Cookie(None)):
    """Check and fix grammar using AI"""
    username = verify_session_token(session) if session else None
    if not username:
        return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    text = data.get('text', '').strip()
    language = data.get('language', 'en')
    
    if not text:
        return JSONResponse({'success': False, 'error': 'Text is required'})
    
    result = await ai_helper.fix_grammar(text, language)
    return JSONResponse(result)

@app.post('/api/ai/example')
async def api_example(request: Request, session: Optional[str] = Cookie(None)):
    """Generate example sentence using AI"""
    username = verify_session_token(session) if session else None
    if not username:
        return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    word = data.get('word', '').strip()
    pos = data.get('pos')
    definition = data.get('definition')
    
    if not word:
        return JSONResponse({'success': False, 'error': 'Word is required'})
    
    result = await ai_helper.generate_example(word, pos, definition)
    return JSONResponse(result)

@app.post('/api/ai/synonyms')
async def api_synonyms(request: Request, session: Optional[str] = Cookie(None)):
    """Get word synonyms (optionally bilingual) using AI/free APIs"""
    username = verify_session_token(session) if session else None
    if not username:
        return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)

    data = await request.json()
    word = data.get('word', '').strip()
    pos = data.get('pos')
    language = data.get('language', 'en')  # 'en' or 'vi'
    translate_to = data.get('translate_to', 'vi')  # target for translation list

    if not word:
        return JSONResponse({'success': False, 'error': 'Word is required'})

    result = await ai_helper.suggest_synonyms(word, pos, language=language, translate_to=translate_to)
    return JSONResponse(result)

@app.post('/api/ai/antonyms')
async def api_antonyms(request: Request, session: Optional[str] = Cookie(None)):
    """Get word antonyms (optionally bilingual) using AI/free APIs"""
    username = verify_session_token(session) if session else None
    if not username:
        return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)

    data = await request.json()
    word = data.get('word', '').strip()
    pos = data.get('pos')
    language = data.get('language', 'en')
    translate_to = data.get('translate_to', 'vi')

    if not word:
        return JSONResponse({'success': False, 'error': 'Word is required'})

    result = await ai_helper.suggest_antonyms(word, pos, language=language, translate_to=translate_to)
    return JSONResponse(result)

@app.get('/api/ai/status')
async def api_ai_status(session: Optional[str] = Cookie(None)):
    """Check if AI features are enabled"""
    username = verify_session_token(session) if session else None
    if not username:
        return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
    
    is_enabled = ai_helper.is_ai_enabled()
    return JSONResponse({
        'success': True,
        'enabled': is_enabled,
        'message': 'AI features are available' if is_enabled else 'Set OPENAI_API_KEY to enable AI features'
    })


# -------------------- Community/Sharing Routes --------------------
@app.get('/browse', response_class=HTMLResponse)
def browse_public_sets(
    request: Request, 
    search: Optional[str] = None,
    language_from: Optional[str] = None,
    language_to: Optional[str] = None,
    session: Optional[str] = Cookie(None)
):
    """Browse public vocabulary sets shared by the community"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    user_obj = get_user(username)
    sets = list_public_sets(search=search, language_from=language_from, language_to=language_to)
    
    return templates.TemplateResponse('browse.html', {
        'request': request,
        'sets': sets,
        'username': username,
        'user': user_obj,
        'search': search,
        'language_from': language_from,
        'language_to': language_to
    })


@app.get('/api/sets/{set_id}/terms')
def api_get_set_terms(set_id: str, session: Optional[str] = Cookie(None)):
    """Get terms for a set (for preview in browse page)"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    vset = get_set(set_id)
    if not vset:
        return JSONResponse({'error': 'Set not found'}, status_code=404)
    
    # Allow access if set is public or user owns it
    if vset.get('visibility') != 'public' and vset.get('user_id') != username:
        return JSONResponse({'error': 'Unauthorized'}, status_code=403)
    
    terms = list_terms(set_id)
    return JSONResponse(terms)


@app.post('/sets/{set_id}/publish')
def publish_set(set_id: str, session: Optional[str] = Cookie(None)):
    """Make a set public or private"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    vset = get_set(set_id)
    if not vset or vset.get('user_id') != username:
        return JSONResponse({'error': 'Unauthorized'}, status_code=403)
    
    # Toggle visibility
    current_visibility = vset.get('visibility', 'private')
    new_visibility = 'public' if current_visibility == 'private' else 'private'
    
    update_set(set_id, visibility=new_visibility)
    
    return RedirectResponse(url=f'/sets/{set_id}', status_code=303)


# -------------------- Feed/Social Routes --------------------
@app.get('/feed', response_class=HTMLResponse)
def feed_page(request: Request, session: Optional[str] = Cookie(None)):
    """Trang feed mạng xã hội - lướt nội dung"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    posts = list_all_feed_items(limit=10, offset=0)
    
    # Add is_liked and is_bookmarked flags for current user
    for post in posts:
        post['is_liked'] = is_liked_by_user(post['id'], username)
        post['is_bookmarked'] = is_bookmarked(post['id'], username)
    
    # Get user's sets for create post dropdown
    user_sets = list_sets(user_id=username)
    user_obj = get_user(username)
    
    # Helper function for time formatting
    def format_time(iso_string):
        if not iso_string:
            return 'Vừa xong'
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(iso_string)
            now = datetime.utcnow()
            diff = (now - dt).total_seconds()
            
            if diff < 60:
                return 'Vừa xong'
            elif diff < 3600:
                return f'{int(diff/60)} phút trước'
            elif diff < 86400:
                return f'{int(diff/3600)} giờ trước'
            elif diff < 604800:
                return f'{int(diff/86400)} ngày trước'
            else:
                return dt.strftime('%d/%m/%Y')
        except:
            return 'Vừa xong'
    
    return templates.TemplateResponse('feed.html', {
        'request': request,
        'posts': posts,
        'username': username,
        'user': user_obj,
        'format_time': format_time,
        'user_sets': user_sets
    })


@app.get('/settings', response_class=HTMLResponse)
def settings_page(request: Request, session: Optional[str] = Cookie(None)):
    """Trang cài đặt tài khoản"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    user_obj = get_user(username)
    
    return templates.TemplateResponse('settings.html', {
        'request': request,
        'username': username,
        'user': user_obj
    })


# -------------------- Profile Routes --------------------

@app.get('/profile', response_class=HTMLResponse)
def profile_page(request: Request, session: Optional[str] = Cookie(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    user_obj = get_user(username)
    return templates.TemplateResponse('profile.html', {
        'request': request,
        'username': username,
        'user': user_obj,
        'message': None,
        'error': None,
    })

@app.post('/profile/update')
async def profile_update(request: Request, session: Optional[str] = Cookie(None),
                         display_name: str = Form(None), email: str = Form(None),
                         avatar: UploadFile = File(None)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)

    avatar_url = None
    if avatar and avatar.filename:
        # Validate extension and size
        name = avatar.filename
        ext = os.path.splitext(name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png']:
            return templates.TemplateResponse('profile.html', {
                'request': request,
                'username': username,
                'user': get_user(username),
                'message': None,
                'error': 'Ảnh đại diện chỉ hỗ trợ JPG/PNG'
            })
        data = await avatar.read()
        if len(data) > 2 * 1024 * 1024:  # 2MB
            return templates.TemplateResponse('profile.html', {
                'request': request,
                'username': username,
                'user': get_user(username),
                'message': None,
                'error': 'Kích thước ảnh vượt quá 2MB'
            })
        import uuid
        filename = f"{username}_{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(avatars_dir, filename)
        with open(save_path, 'wb') as f:
            f.write(data)
        avatar_url = f"/static/avatars/{filename}"

    updated = update_user_profile(username, display_name=display_name, email=email, avatar=avatar_url)
    return templates.TemplateResponse('profile.html', {
        'request': request,
        'username': username,
        'user': updated or get_user(username),
        'message': 'Cập nhật hồ sơ thành công',
        'error': None
    })

@app.post('/profile/change-password')
async def profile_change_password(request: Request, session: Optional[str] = Cookie(None),
                                  current_password: str = Form(...),
                                  new_password: str = Form(...),
                                  new_password2: str = Form(...)):
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    if new_password != new_password2:
        return templates.TemplateResponse('profile.html', {
            'request': request,
            'username': username,
            'user': get_user(username),
            'message': None,
            'error': 'Mật khẩu mới không khớp'
        })
    ok = change_user_password(username, current_password, new_password)
    if not ok:
        return templates.TemplateResponse('profile.html', {
            'request': request,
            'username': username,
            'user': get_user(username),
            'message': None,
            'error': 'Mật khẩu hiện tại không đúng'
        })
    return templates.TemplateResponse('profile.html', {
        'request': request,
        'username': username,
        'user': get_user(username),
        'message': 'Đổi mật khẩu thành công',
        'error': None
    })


@app.get('/api/feed')
def api_get_feed(page: int = 1, limit: int = 10, session: Optional[str] = Cookie(None)):
    """API lấy feed posts với pagination"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    offset = (page - 1) * limit
    posts = list_all_feed_items(limit=limit, offset=offset)
    
    # Add is_liked flag
    for post in posts:
        post['is_liked'] = is_liked_by_user(post['id'], username)
    
    return JSONResponse({'posts': posts, 'page': page, 'has_more': len(posts) == limit})


@app.post('/api/upload/image')
async def upload_image(file: UploadFile = File(...), session: Optional[str] = Cookie(None)):
    """Upload ảnh cho post"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        return JSONResponse({'error': 'File phải là ảnh'}, status_code=400)
    
    # Validate file size (5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        return JSONResponse({'error': 'Ảnh không được vượt quá 5MB'}, status_code=400)
    
    # Save file with unique name
    import hashlib
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    file_hash = hashlib.md5(content).hexdigest()[:16]
    filename = f"{username}_{file_hash}.{file_ext}"
    filepath = os.path.join(uploads_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(content)
    
    # Return URL
    image_url = f"/static/uploads/{filename}"
    return JSONResponse({'success': True, 'url': image_url})


@app.post('/api/posts/create')
async def api_create_post(request: Request, session: Optional[str] = Cookie(None)):
    """Tạo bài viết mới lên feed"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    content = data.get('content', '').strip()
    attached_set_id = data.get('attached_set_id')
    image_url = data.get('image_url')
    
    if not content and not image_url:
        return JSONResponse({'error': 'Nội dung hoặc ảnh không được để trống'}, status_code=400)
    
    # Validate attached set if provided
    if attached_set_id:
        vset = get_set(attached_set_id)
        if not vset or vset.get('user_id') != username:
            return JSONResponse({'error': 'Bộ từ không hợp lệ'}, status_code=400)
    
    post = create_post(username, username, content, attached_set_id, image_url)
    
    return JSONResponse({
        'success': True,
        'post': post
    })


@app.post('/api/sets/{set_id}/like')
async def api_like_set(set_id: str, request: Request, session: Optional[str] = Cookie(None)):
    """Thích/Bỏ thích bộ từ hoặc post"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    # Check if it's a set or post
    vset = get_set(set_id)
    if not vset:
        # Maybe it's a post, allow liking
        pass
    elif vset.get('visibility') != 'public':
        return JSONResponse({'error': 'Set not found or not public'}, status_code=404)
    
    data = await request.json()
    unlike = data.get('unlike', False)
    
    if unlike:
        remove_like(set_id, username)
        liked = False
    else:
        add_like(set_id, username)
        liked = True
    
    likes_count = get_likes_count(set_id)
    
    return JSONResponse({
        'success': True,
        'liked': liked,
        'likes_count': likes_count
    })


@app.post('/api/sets/{set_id}/comment')
async def api_comment_set(set_id: str, request: Request, session: Optional[str] = Cookie(None)):
    """Bình luận vào bộ từ (public) hoặc bài viết text.

    Trước đây endpoint này CHỈ cho phép comment vào bộ từ public, khiến không thể comment
    lên bài viết text_post trên feed. Đồng thời người dùng hiểu nhầm là bị giới hạn chỉ 1
    bình luận hoặc 1 trả lời. Thực tế backend không giới hạn, mà do endpoint từ chối bài viết.

    Cập nhật: Cho phép nếu:
      - set_id thuộc về 1 bộ từ public (giữ điều kiện cũ) HOẶC
      - set_id trùng id của một text post (get_post trả về dữ liệu)
    Nếu cả hai đều không tồn tại => 404.
    """
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)

    vset = get_set(set_id)
    post_obj = None
    if not vset:
        # Thử coi đây là bài viết text
        post_obj = get_post(set_id)

    # Nếu là set thì phải public; nếu là post thì cho phép luôn
    if vset:
        if vset.get('visibility') != 'public':
            return JSONResponse({'error': 'Set not found or not public'}, status_code=404)
    elif not post_obj:
        return JSONResponse({'error': 'Target not found'}, status_code=404)

    data = await request.json()
    content = data.get('content', '').strip()
    if not content:
        return JSONResponse({'error': 'Comment cannot be empty'}, status_code=400)

    # Lưu comment dùng chung trường set_id (giữ schema cũ) – có thể là id của set hoặc post
    comment = add_comment(set_id, username, username, content)
    comments_count = get_comments_count(set_id)

    return JSONResponse({'success': True, 'comment': comment, 'comments_count': comments_count})


@app.get('/api/sets/{set_id}/comments')
async def api_get_comments(set_id: str, session: Optional[str] = Cookie(None)):
    """Lấy danh sách bình luận cho set public hoặc bài viết text.

    Không giới hạn số lượng (front-end có thể scroll). Có thể mở rộng sau bằng query params
    để phân trang nếu cần (page, limit).
    """
    username = get_current_user(session)

    # Cho phép nếu tồn tại set public HOẶC là post
    vset = get_set(set_id)
    if vset and vset.get('visibility') != 'public':
        return JSONResponse({'error': 'Set not public'}, status_code=403)
    if not vset:
        post_obj = get_post(set_id)
        if not post_obj:
            return JSONResponse({'error': 'Target not found'}, status_code=404)

    comments = get_comments(set_id)

    from .auth import get_user as _get_user
    for comment in comments:
        user_info = _get_user(comment.get('username'))
        if user_info:
            comment['user_avatar'] = user_info.get('avatar')
            comment['user_display_name'] = user_info.get('display_name') or comment.get('username')
        comment['likes_count'] = get_comment_likes_count(comment['id'])
        comment['is_liked'] = is_comment_liked(comment['id'], username) if username else False
        comment['replies_count'] = get_comment_replies_count(comment['id'])
        comment['replies'] = get_comment_replies(comment['id'])
        for reply in comment['replies']:
            reply_user = _get_user(reply.get('username'))
            if reply_user:
                reply['user_avatar'] = reply_user.get('avatar')
                reply['user_display_name'] = reply_user.get('display_name') or reply.get('username')

    return JSONResponse(comments)


@app.post('/api/sets/{set_id}/clone')
async def api_clone_set(set_id: str, request: Request, session: Optional[str] = Cookie(None)):
    """Sao chép bộ từ vào tài khoản của mình"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    # Get caption if provided
    try:
        data = await request.json()
        caption = data.get('caption')
    except:
        caption = None
    
    vset = get_set(set_id)
    if not vset:
        return JSONResponse({'error': 'Set not found'}, status_code=404)
    
    try:
        new_set_id = clone_set(set_id, username, username)
        add_share(set_id, username)  # Track as a share
        
        # If caption provided, could create a post about the shared set
        # (Future enhancement: create a post with the caption)
        
        return JSONResponse({
            'success': True,
            'new_set_id': new_set_id
        })
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ---- Bookmark APIs ----
@app.post('/api/sets/{set_id}/bookmark')
async def api_bookmark_set(set_id: str, session: Optional[str] = Cookie(None)):
    """Lưu/bỏ lưu bộ từ hoặc post"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    # Check if it's a set or post - allow bookmarking either
    vset = get_set(set_id)
    if not vset:
        # Maybe it's a post, allow bookmarking
        pass
    
    is_saved = is_bookmarked(set_id, username)
    
    if is_saved:
        remove_bookmark(set_id, username)
        saved = False
    else:
        add_bookmark(set_id, username)
        saved = True
    
    return JSONResponse({
        'success': True,
        'saved': saved
    })


@app.get('/api/bookmarks')
async def api_get_bookmarks(session: Optional[str] = Cookie(None)):
    """Lấy danh sách bộ từ đã lưu"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    bookmarks = get_user_bookmarks(username)
    return JSONResponse(bookmarks)


# ---- Comment Like/Reply APIs ----
@app.post('/api/comments/{comment_id}/like')
async def api_like_comment(comment_id: str, session: Optional[str] = Cookie(None)):
    """Thích/bỏ thích bình luận"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    is_liked = is_comment_liked(comment_id, username)
    
    if is_liked:
        remove_comment_like(comment_id, username)
        liked = False
    else:
        add_comment_like(comment_id, username)
        liked = True
    
    likes_count = get_comment_likes_count(comment_id)
    
    return JSONResponse({
        'success': True,
        'liked': liked,
        'likes_count': likes_count
    })


@app.post('/api/comments/{comment_id}/reply')
async def api_reply_comment(comment_id: str, request: Request, session: Optional[str] = Cookie(None)):
    """Trả lời bình luận"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    content = data.get('content', '').strip()
    
    if not content:
        return JSONResponse({'error': 'Reply cannot be empty'}, status_code=400)
    
    reply = add_comment_reply(comment_id, username, username, content)
    replies_count = get_comment_replies_count(comment_id)
    
    # Add user info
    from .auth import get_user
    user_info = get_user(username)
    if user_info:
        reply['user_avatar'] = user_info.get('avatar')
        reply['user_display_name'] = user_info.get('display_name') or username
    
    return JSONResponse({
        'success': True,
        'reply': reply,
        'replies_count': replies_count
    })


# ========== Post Management APIs ==========

@app.delete('/api/posts/{post_id}')
async def api_delete_post(post_id: str, session: Optional[str] = Cookie(None)):
    """Xóa bài viết"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    success = delete_post(post_id, username)
    if success:
        return JSONResponse({'success': True, 'message': 'Đã xóa bài viết'})
    else:
        return JSONResponse({'error': 'Cannot delete post'}, status_code=403)


@app.put('/api/posts/{post_id}')
async def api_update_post(post_id: str, request: Request, session: Optional[str] = Cookie(None)):
    """Chỉnh sửa bài viết"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    content = data.get('content', '').strip()
    image_url = data.get('image_url')
    
    if not content:
        return JSONResponse({'error': 'Content cannot be empty'}, status_code=400)
    
    success = update_post(post_id, username, content, image_url)
    if success:
        post = get_post(post_id)
        return JSONResponse({'success': True, 'message': 'Đã cập nhật bài viết', 'post': post})
    else:
        return JSONResponse({'error': 'Cannot update post'}, status_code=403)


# ========== Comment Management APIs ==========

@app.delete('/api/comments/{comment_id}')
async def api_delete_comment(comment_id: str, session: Optional[str] = Cookie(None)):
    """Xóa bình luận"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    success = delete_comment(comment_id, username)
    if success:
        return JSONResponse({'success': True, 'message': 'Đã xóa bình luận'})
    else:
        return JSONResponse({'error': 'Cannot delete comment'}, status_code=403)


@app.put('/api/comments/{comment_id}')
async def api_update_comment(comment_id: str, request: Request, session: Optional[str] = Cookie(None)):
    """Chỉnh sửa bình luận"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    content = data.get('content', '').strip()
    
    if not content:
        return JSONResponse({'error': 'Content cannot be empty'}, status_code=400)
    
    success = update_comment(comment_id, username, content)
    if success:
        return JSONResponse({'success': True, 'message': 'Đã cập nhật bình luận'})
    else:
        return JSONResponse({'error': 'Cannot update comment'}, status_code=403)


# ========== Reply Management APIs ==========

@app.delete('/api/replies/{reply_id}')
async def api_delete_reply(reply_id: str, session: Optional[str] = Cookie(None)):
    """Xóa trả lời"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    success = delete_reply(reply_id, username)
    if success:
        return JSONResponse({'success': True, 'message': 'Đã xóa trả lời'})
    else:
        return JSONResponse({'error': 'Cannot delete reply'}, status_code=403)


@app.put('/api/replies/{reply_id}')
async def api_update_reply(reply_id: str, request: Request, session: Optional[str] = Cookie(None)):
    """Chỉnh sửa trả lời"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    content = data.get('content', '').strip()
    
    if not content:
        return JSONResponse({'error': 'Content cannot be empty'}, status_code=400)
    
    success = update_reply(reply_id, username, content)
    if success:
        return JSONResponse({'success': True, 'message': 'Đã cập nhật trả lời'})
    else:
        return JSONResponse({'error': 'Cannot update reply'}, status_code=403)



@app.get('/test-oauth')
async def test_oauth():
    """Test route"""
    print('TEST ROUTE CALLED!')
    return {'message': 'OAuth test route works!'}

@app.get('/auth/google')
async def auth_google(request: Request):
    """Bắt đầu OAuth flow với Google"""
    print('='*50)
    print('DEBUG: /auth/google called')
    print('='*50)
    try:
        client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        print(f'DEBUG: GOOGLE_CLIENT_ID = "{client_id}"')
        print(f'DEBUG: Length = {len(client_id)}')
        
        # Kiểm tra xem có cấu hình OAuth không
        if not client_id or client_id.strip() == 'your-google-client-id-here':
            print('DEBUG: OAuth not configured')
            return RedirectResponse('/login?error=oauth_not_configured')
        
        print('DEBUG: Starting OAuth redirect...')
        redirect_uri = request.url_for('auth_google_callback')
        print(f'DEBUG: Redirect URI: {redirect_uri}')
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        print(f'Google OAuth error: {e}')
        import traceback
        traceback.print_exc()
        return RedirectResponse('/login?error=oauth_failed')


@app.get('/auth/google/callback')
async def auth_google_callback(request: Request):
    """Xử lý callback từ Google OAuth"""
    print('='*50)
    print('DEBUG: /auth/google/callback called')
    print(f'DEBUG: Query params: {request.query_params}')
    print('='*50)
    try:
        print('DEBUG: Google callback received')
        token = await oauth.google.authorize_access_token(request)
        print(f'DEBUG: Token received: {bool(token)}')
        
        user_info = token.get('userinfo')
        print(f'DEBUG: User info: {user_info}')
        
        if not user_info:
            print('DEBUG: No user info!')
            return RedirectResponse('/login?error=oauth_failed')
        
        # Extract user data
        email = user_info.get('email')
        google_id = user_info.get('sub')
        name = user_info.get('name', email.split('@')[0] if email else 'user')
        
        print(f'DEBUG: Creating user - google_{google_id}')
        
        # Check if user exists with this Google ID
        username = f'google_{google_id}'
        user = get_user(username)
        
        if not user:
            print('DEBUG: User not found, creating new user')
            # Create new user with Google OAuth
            try:
                create_user(username, 'oauth_google', email=email)
                print('DEBUG: User created successfully')
            except Exception as e:
                print(f'DEBUG: Error creating user: {e}')
                # User might exist, try to login anyway
                pass
        else:
            print('DEBUG: User already exists')
        
        # Create session
        session_token = create_session_token(username)
        print(f'DEBUG: Session token created: {bool(session_token)}')
        print(f'DEBUG: Session token value: {session_token[:20]}...')
        
        response = RedirectResponse('/dashboard', status_code=302)
        response.set_cookie(
            key='session',
            value=session_token,
            httponly=True,
            max_age=7*24*60*60,
            path='/',
            samesite='lax'
        )
        print('DEBUG: Cookie set, redirecting to dashboard')
        return response
        
    except Exception as e:
        print(f'Google OAuth callback error: {e}')
        import traceback
        traceback.print_exc()
        return RedirectResponse('/login?error=oauth_failed')


@app.get('/auth/github')
async def auth_github(request: Request):
    """Bắt đầu OAuth flow với GitHub"""
    try:
        client_id = os.getenv('GITHUB_CLIENT_ID', '')
        print(f'DEBUG: GITHUB_CLIENT_ID = "{client_id}"')
        
        # Kiểm tra xem có cấu hình OAuth không
        if not client_id or client_id.strip() == 'your-github-client-id-here':
            print('DEBUG: GitHub OAuth not configured')
            return RedirectResponse('/login?error=oauth_not_configured')
        
        print('DEBUG: Starting GitHub OAuth redirect...')
        redirect_uri = request.url_for('auth_github_callback')
        return await oauth.github.authorize_redirect(request, redirect_uri)
    except Exception as e:
        print(f'GitHub OAuth error: {e}')
        import traceback
        traceback.print_exc()
        return RedirectResponse('/login?error=oauth_failed')


@app.get('/auth/github/callback')
async def auth_github_callback(request: Request):
    """Xử lý callback từ GitHub OAuth"""
    try:
        token = await oauth.github.authorize_access_token(request)
        
        # Get user info from GitHub API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f'Bearer {token["access_token"]}'}
            )
            user_info = response.json()
        
        github_id = str(user_info.get('id'))
        github_login = user_info.get('login')
        email = user_info.get('email')
        
        # Check if user exists with this GitHub ID
        username = f'github_{github_id}'
        user = get_user(username)
        
        if not user:
            # Create new user with GitHub OAuth
            try:
                create_user(username, 'oauth_github', email=email)
            except Exception as e:
                pass
        
        # Create session
        session_token = create_session_token(username)
        response = RedirectResponse('/dashboard')
        response.set_cookie('session', session_token, httponly=True, max_age=7*24*60*60)
        return response
        
    except Exception as e:
        print(f'GitHub OAuth error: {e}')
        return RedirectResponse('/login?error=oauth_failed')


@app.get('/auth/twitter')
async def auth_twitter(request: Request):
    """Bắt đầu OAuth flow với Twitter"""
    try:
        client_id = os.getenv('TWITTER_CLIENT_ID', '')
        print(f'DEBUG: TWITTER_CLIENT_ID = "{client_id}"')
        
        # Kiểm tra xem có cấu hình OAuth không
        if not client_id or client_id.strip() == 'your-twitter-client-id-here':
            print('DEBUG: Twitter OAuth not configured')
            return RedirectResponse('/login?error=oauth_not_configured')
        
        print('DEBUG: Starting Twitter OAuth redirect...')
        redirect_uri = request.url_for('auth_twitter_callback')
        return await oauth.twitter.authorize_redirect(request, redirect_uri)
    except Exception as e:
        print(f'Twitter OAuth error: {e}')
        import traceback
        traceback.print_exc()
        return RedirectResponse('/login?error=oauth_failed')


@app.get('/auth/twitter/callback')
async def auth_twitter_callback(request: Request):
    """Xử lý callback từ Twitter OAuth"""
    try:
        token = await oauth.twitter.authorize_access_token(request)
        
        # Get user info from Twitter API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.twitter.com/2/users/me',
                headers={'Authorization': f'Bearer {token["access_token"]}'}
            )
            user_data = response.json()
            user_info = user_data.get('data', {})
        
        twitter_id = user_info.get('id')
        twitter_username = user_info.get('username')
        
        # Check if user exists with this Twitter ID
        username = f'twitter_{twitter_id}'
        user = get_user(username)
        
        if not user:
            # Create new user with Twitter OAuth
            try:
                create_user(username, 'oauth_twitter', email=None)
            except Exception as e:
                pass
        
        # Create session
        session_token = create_session_token(username)
        response = RedirectResponse('/dashboard')
        response.set_cookie('session', session_token, httponly=True, max_age=7*24*60*60)
        return response
        
    except Exception as e:
        print(f'Twitter OAuth error: {e}')
        return RedirectResponse('/login?error=oauth_failed')


# -------------------- User Profile Routes --------------------

@app.get('/user/{target_username}', response_class=HTMLResponse)
def user_profile_page(target_username: str, request: Request, session: Optional[str] = Cookie(None)):
    """Xem trang cá nhân của người dùng"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    # Get profile user info
    profile_user = get_user(target_username)
    if not profile_user:
        return HTMLResponse('<h1>Người dùng không tồn tại</h1>', status_code=404)
    
    # Get current user info
    user_obj = get_user(username)
    
    # Check if viewing own profile
    is_own_profile = (username == target_username)
    
    # Get follower/following stats
    followers = get_followers(target_username)
    following = get_following(target_username)
    followers_count = len(followers)
    following_count = len(following)
    
    # Check if current user is following target user
    is_following_user = is_following(username, target_username) if not is_own_profile else False
    
    # Get user's sets count
    user_sets = list_sets(user_id=target_username)
    sets_count = len(user_sets)
    
    # Get user's posts (text posts only, not vocab sets)
    from .storage import get_user_posts
    posts = get_user_posts(target_username, limit=20)

    # Add liked/saved flags similar to feed for current viewer
    try:
        for p in posts:
            p['is_liked'] = is_liked_by_user(p['id'], username)
            p['is_bookmarked'] = is_bookmarked(p['id'], username)
            # Populate social stats for consistency with feed
            p['likes_count'] = get_likes_count(p['id'])
            p['comments_count'] = get_comments_count(p['id'])
            p['shares_count'] = get_shares_count(p['id'])
    except Exception:
        pass
    
    # Format time function
    def format_time(dt_str):
        if not dt_str:
            return 'Gần đây'
        try:
            dt = datetime.fromisoformat(dt_str)
            now = datetime.now()
            diff = (now - dt).total_seconds()
            
            if diff < 60:
                return 'Vừa xong'
            elif diff < 3600:
                return f'{int(diff / 60)} phút trước'
            elif diff < 86400:
                return f'{int(diff / 3600)} giờ trước'
            elif diff < 604800:
                return f'{int(diff / 86400)} ngày trước'
            else:
                return dt.strftime('%d/%m/%Y')
        except:
            return 'Gần đây'
    
    return templates.TemplateResponse('user_profile.html', {
        'request': request,
        'username': username,
        'user': user_obj,
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'followers_count': followers_count,
        'following_count': following_count,
        'sets_count': sets_count,
        'is_following': is_following_user,
        'posts': posts,
        'format_time': format_time,
    })


@app.post('/api/users/{target_username}/follow')
async def api_follow_user(target_username: str, request: Request, session: Optional[str] = Cookie(None)):
    """Follow/Unfollow người dùng"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    if username == target_username:
        return JSONResponse({'error': 'Không thể follow chính mình'}, status_code=400)
    
    data = await request.json()
    unfollow = data.get('unfollow', False)
    
    if unfollow:
        success = unfollow_user(username, target_username)
    else:
        success = follow_user(username, target_username)
    
    if not success:
        return JSONResponse({'error': 'Không thể thực hiện'}, status_code=400)
    
    return JSONResponse({
        'success': True,
        'is_following': not unfollow
    })


@app.post('/api/profile/update')
async def api_update_profile(request: Request, session: Optional[str] = Cookie(None)):
    """Cập nhật thông tin cá nhân"""
    username = get_current_user(session)
    if not username:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    data = await request.json()
    display_name = data.get('display_name')
    bio = data.get('bio')
    location = data.get('location')
    website = data.get('website')
    facebook = data.get('facebook')
    instagram = data.get('instagram')
    twitter = data.get('twitter')
    school = data.get('school')
    
    updated = update_user_profile(
        username,
        display_name=display_name,
        bio=bio,
        location=location,
        website=website,
        facebook=facebook,
        instagram=instagram,
        twitter=twitter,
        school=school
    )
    
    if updated:
        return JSONResponse({'success': True, 'user': updated})
    else:
        return JSONResponse({'error': 'Không thể cập nhật'}, status_code=400)


@app.get('/user/{target_username}/sets', response_class=HTMLResponse)
def user_profile_sets_page(target_username: str, request: Request, session: Optional[str] = Cookie(None)):
    """Xem trang bộ từ của người dùng"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    # Get profile user info
    profile_user = get_user(target_username)
    if not profile_user:
        return HTMLResponse('<h1>Người dùng không tồn tại</h1>', status_code=404)
    
    # Get current user info
    user_obj = get_user(username)
    
    # Check if viewing own profile
    is_own_profile = (username == target_username)
    
    # Get follower/following stats
    followers_count = len(get_followers(target_username))
    following_count = len(get_following(target_username))
    
    # Get user's sets
    user_sets = list_sets(user_id=target_username)
    
    # Add stats to each set
    for s in user_sets:
        terms = list_terms(s['id'])
        s['term_count'] = len(terms)
        s['likes_count'] = get_likes_count(s['id'])
        s['comments_count'] = get_comments_count(s['id'])
        s['shares_count'] = get_shares_count(s['id'])
    
    # Filter by visibility if not own profile
    if not is_own_profile:
        user_sets = [s for s in user_sets if s.get('visibility') == 'public']
    
    sets_count = len(user_sets)
    public_count = len([s for s in user_sets if s.get('visibility') == 'public'])
    private_count = len([s for s in user_sets if s.get('visibility') == 'private'])
    
    return templates.TemplateResponse('user_profile_sets.html', {
        'request': request,
        'username': username,
        'user': user_obj,
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'followers_count': followers_count,
        'following_count': following_count,
        'sets_count': sets_count,
        'public_count': public_count,
        'private_count': private_count,
        'sets': user_sets,
    })


@app.get('/user/{target_username}/about', response_class=HTMLResponse)
def user_profile_about_page(target_username: str, request: Request, session: Optional[str] = Cookie(None)):
    """Xem trang giới thiệu của người dùng"""
    username = get_current_user(session)
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    
    # Get profile user info
    profile_user = get_user(target_username)
    if not profile_user:
        return HTMLResponse('<h1>Người dùng không tồn tại</h1>', status_code=404)
    
    # Get current user info
    user_obj = get_user(username)
    
    # Check if viewing own profile
    is_own_profile = (username == target_username)
    
    # Get follower/following stats
    followers_count = len(get_followers(target_username))
    following_count = len(get_following(target_username))
    
    # Get user's sets count and total terms
    user_sets = list_sets(user_id=target_username)
    sets_count = len(user_sets)
    
    total_terms = 0
    for s in user_sets:
        terms = list_terms(s['id'])
        total_terms += len(terms)
    
    # Get recent activities (sample data - can be enhanced later)
    recent_activities = []
    
    # Add recent sets as activities
    sorted_sets = sorted(user_sets, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    for s in sorted_sets:
        try:
            from datetime import datetime
            created = datetime.fromisoformat(s.get('created_at', ''))
            date_str = created.strftime('%d/%m/%Y %H:%M')
        except:
            date_str = 'Gần đây'
        
        recent_activities.append({
            'icon': '📚',
            'title': f'Tạo bộ từ "{s["name"]}"',
            'description': f'{s.get("description", "Không có mô tả")[:50]}...' if len(s.get("description", "")) > 50 else s.get("description", ""),
            'date': date_str
        })
    
    return templates.TemplateResponse('user_profile_about.html', {
        'request': request,
        'username': username,
        'user': user_obj,
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'followers_count': followers_count,
        'following_count': following_count,
        'sets_count': sets_count,
        'total_terms': total_terms,
        'recent_activities': recent_activities,
    })


