import csv, io
from typing import List, Dict, Tuple
try:
    import openpyxl  # type: ignore
except Exception:
    openpyxl = None

HEADER_HINTS = {
    'word': ['từ', 'từ vựng', 'term', 'word', 'english', 'vocabulary', 'từ tiếng anh', 'vocab'],
    'pos': ['loại từ', 'từ loại', 'pos', 'part of speech', 'word type', 'type'],
    'meaning': ['nghĩa', 'định nghĩa', 'definition', 'meaning', 'translation', 'dịch', 'tiếng việt', 'vietnamese'],
    'pronunciation': ['phiên âm', 'phát âm', 'pronunciation', 'phonetic', 'ipa', 'transcription'],
    'example': ['ví dụ', 'ví du', 'example', 'sample', 'sentence', 'usage', 'câu ví dụ']
}

POS_VALUES = set([
    'n', 'n.', 'noun', 'danh từ', 'danh tu',
    'v', 'v.', 'verb', 'động từ', 'dong tu',
    'adj', 'adj.', 'adjective', 'tính từ', 'tinh tu',
    'adv', 'adv.', 'adverb', 'trạng từ', 'trang tu',
    'prep', 'prep.', 'preposition', 'giới từ', 'gioi tu',
    'conj', 'conj.', 'conjunction', 'liên từ', 'lien tu',
    'pron', 'pron.', 'pronoun', 'đại từ', 'dai tu',
    'num', 'numeral', 'số từ', 'so tu',
    'phr', 'phr.', 'phrase', 'cụm từ', 'cum tu',
])


def has_vietnamese(text: str) -> bool:
    """Check if text contains Vietnamese diacritics"""
    for ch in text:
        oc = ord(ch)
        if ch in 'ăâêôơưđĂÂÊÔƠƯĐ' or 192 <= oc <= 7929:
            return True
    return False


def _has_vietnamese_chars(text: str) -> bool:
    """More accurate Vietnamese detection"""
    vn_chars = 'ăâêôơưđĂÂÊÔƠƯĐáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ'
    return any(ch in vn_chars for ch in text)


def is_pos_value(s: str) -> bool:
    s = (s or '').strip().lower()
    if s.endswith('.'):
        s = s[:-1]
    return s in POS_VALUES


def sniff_csv_bytes(b: bytes) -> List[Dict[str, str]]:
    for enc in ('utf-8-sig', 'utf-8', 'cp1258', 'cp1252', 'latin-1'):
        try:
            text = b.decode(enc)
            f = io.StringIO(text)
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows and reader.fieldnames:
                return rows
        except Exception:
            continue
    raise ValueError('CSV encoding không hỗ trợ')


def read_xlsx_bytes(b: bytes) -> List[Dict[str, str]]:
    if openpyxl is None:
        raise ValueError('Thiếu openpyxl để đọc XLSX')
    bio = io.BytesIO(b)
    wb = openpyxl.load_workbook(bio, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip() if h is not None else '' for h in rows[0]]
    data = []
    for r in rows[1:]:
        rec = {}
        for i, h in enumerate(headers):
            val = r[i] if i < len(r) else None
            rec[h or f'c{i+1}'] = '' if val is None else str(val)
        data.append(rec)
    return data


def score_headers(headers: List[str]) -> Dict[str, Dict[str, float]]:
    scores = {h: {'word': 0.0, 'pos': 0.0, 'meaning': 0.0, 'pronunciation': 0.0, 'example': 0.0} for h in headers}
    for h in headers:
        hl = h.lower()
        for cat, hints in HEADER_HINTS.items():
            for kw in hints:
                if kw in hl:
                    scores[h][cat] += 2.0
    return scores


def score_content(rows: List[Dict[str, str]], headers: List[str]) -> Dict[str, Dict[str, float]]:
    scores = {h: {'word': 0.0, 'pos': 0.0, 'meaning': 0.0, 'pronunciation': 0.0, 'example': 0.0} for h in headers}
    sample = rows[: min(50, len(rows))]
    for h in headers:
        word_hits = pos_hits = meaning_hits = pronunciation_hits = example_hits = 0
        total = 0
        for r in sample:
            s = (r.get(h) or '').strip()
            if not s:
                continue
            total += 1
            # pos detection - very strict
            if is_pos_value(s):
                pos_hits += 1
            # pronunciation: contains IPA chars or starts with / or [ brackets
            if any(c in s for c in ['ə', 'ɪ', 'ʊ', 'ɔ', 'ɑ', 'æ', 'ʌ', 'ɜ', 'θ', 'ð', 'ʃ', 'ʒ', 'ŋ']) or s.startswith(('/', '[')):
                pronunciation_hits += 1
            # example: longer sentences (>5 words) or contains sentence patterns
            if len(s.split()) >= 5 or any(pattern in s.lower() for pattern in ['.', '!', '?', 'e.g', 'ex:', 'ví dụ']):
                example_hits += 1
            # meaning: longer text OR Vietnamese OR starts with uppercase Vietnamese letter
            if _has_vietnamese_chars(s) or len(s.split()) >= 4 or len(s) > 30:
                meaning_hits += 1
            # word: short (1-3 words), mostly lowercase English, no Vietnamese
            if len(s.split()) <= 3 and not _has_vietnamese_chars(s) and len(s) < 25:
                word_hits += 1
        if total:
            # Boost POS score heavily if high match rate
            if pos_hits / total >= 0.7:
                scores[h]['pos'] += 10.0
            else:
                scores[h]['pos'] += 3.0 * (pos_hits / total)
            scores[h]['pronunciation'] += 2.5 * (pronunciation_hits / total)
            scores[h]['example'] += 2.0 * (example_hits / total)
            scores[h]['meaning'] += 2.5 * (meaning_hits / total)
            scores[h]['word'] += 2.0 * (word_hits / total)
    return scores


def _has_vietnamese_chars(text: str) -> bool:
    """More accurate Vietnamese detection"""
    vn_chars = 'ăâêôơưđĂÂÊÔƠƯĐáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ'
    return any(ch in vn_chars for ch in text)


def choose_mapping(rows: List[Dict[str, str]]) -> Tuple[dict, List[str]]:
    if not rows:
        return {}, []
    headers = list(rows[0].keys())
    hs = score_headers(headers)
    cs = score_content(rows, headers)
    combined = {h: {k: hs[h][k] + cs[h][k] for k in ['word', 'pos', 'meaning', 'pronunciation', 'example']} for h in headers}
    assigned = {}
    used = set()
    
    # Priority order: pos first (most distinctive), then word, meaning, pronunciation, example
    for cat in ['pos', 'word', 'meaning', 'pronunciation', 'example']:
        best_col = None
        best_score = 0.0
        for h in headers:
            if h in used:
                continue
            sc = combined[h][cat]
            if sc > best_score:
                best_score = sc
                best_col = h
        # Different thresholds for each category
        if cat == 'pos':
            thresh = 2.0  # POS needs strong signal
        elif cat == 'word':
            thresh = 0.8
        elif cat == 'pronunciation':
            thresh = 0.5  # Lower threshold for optional field
        elif cat == 'example':
            thresh = 0.5  # Lower threshold for optional field
        else:  # meaning
            thresh = 0.8
        if best_col and best_score >= thresh:
            assigned[cat] = best_col
            used.add(best_col)
    
    return assigned, headers


async def read_any(file) -> List[Dict[str, str]]:
    b = await file.read()
    name = file.filename.lower()
    if name.endswith('.csv'):
        return sniff_csv_bytes(b)
    if name.endswith('.xlsx'):
        return read_xlsx_bytes(b)
    try:
        return sniff_csv_bytes(b)
    except Exception:
        raise ValueError('Định dạng file không hỗ trợ (.csv/.xlsx)')
