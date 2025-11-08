"""
AI Helper Module for VocabApp
Provides translation, grammar checking, and example generation using
OpenAI when available, with free fallbacks (googletrans, LanguageTool, Datamuse)
so the app can be tested without a paid key.
"""
import os
from typing import Optional, Dict, Any, List
import openai
import requests

# Get API key from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
openai.api_key = OPENAI_API_KEY


def _has_openai() -> bool:
    return bool(OPENAI_API_KEY)


def _has_free_translation() -> bool:
    # We use MyMemory API (no install needed), so always True for free translation
    return True


def is_ai_enabled() -> bool:
    """Check if ANY AI features are available (OpenAI or free providers)."""
    return _has_openai() or _has_free_translation()


# -------- Simple Translation Helper (MyMemory) --------
def _translate_mymemory(text: str, src: str, dst: str) -> Optional[str]:
    try:
        s = (src or 'en')[:2]
        d = (dst or 'vi')[:2]
        r = requests.get(
            'https://api.mymemory.translated.net/get',
            params={'q': text, 'langpair': f'{s}|{d}'},
            timeout=15,
        )
        r.raise_for_status()
        j = r.json()
        return j.get('responseData', {}).get('translatedText')
    except Exception:
        return None

def _translate_list(words: List[str], src: str, dst: str, limit: int = 5) -> List[str]:
    out: List[str] = []
    for w in words[:limit]:
        tr = _translate_mymemory(w, src, dst)
        out.append(tr or w)
    return out

async def translate_text(text: str, from_lang: str = 'en', to_lang: str = 'vi') -> Dict[str, Any]:
    """
    Translate text from one language to another
    
    Args:
        text: Text to translate
        from_lang: Source language code (en, vi, etc.)
        to_lang: Target language code
    
    Returns:
        Dict with 'translation' and 'success' keys
    """
    # Prefer OpenAI if configured
    if _has_openai():
        try:
            # Use OpenAI Chat API for translation
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate from {from_lang} to {to_lang}. Only provide the translation, no explanations."
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=200,
            )

            translation = response.choices[0].message.content.strip()
            return {
                'success': True,
                'translation': translation,
                'original': text,
                'provider': 'openai'
            }
        except Exception as e:
            # Fall through to free provider
            last_err = str(e)
    else:
        last_err = None

    # Free fallback: MyMemory API (rate-limited, public)
    try:
        # Constrain language codes to 2-letter pairs for MyMemory
        src = (from_lang or 'en')[:2]
        dst = (to_lang or 'vi')[:2]
        r = requests.get(
            'https://api.mymemory.translated.net/get',
            params={'q': text, 'langpair': f'{src}|{dst}'},
            timeout=15,
        )
        r.raise_for_status()
        j = r.json()
        trans = j.get('responseData', {}).get('translatedText')
        if trans:
            return {
                'success': True,
                'translation': trans,
                'original': text,
                'provider': 'mymemory'
            }
        last_err = j.get('responseDetails') or 'Translation failed'
    except Exception as e:
        last_err = str(e)

    return {
        'success': False,
        'error': last_err or 'No translation provider available (install googletrans or set OPENAI_API_KEY)'
    }

async def fix_grammar(text: str, language: str = 'en') -> Dict[str, Any]:
    """
    Check and fix grammar errors in text
    
    Args:
        text: Text to check
        language: Language code (en, vi)
    
    Returns:
        Dict with 'corrected', 'errors', and 'success' keys
    """
    # Prefer OpenAI if available
    if _has_openai():
        try:
            lang_name = "English" if language == "en" else "Vietnamese"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a {lang_name} grammar expert. Check and correct grammar errors. Provide the corrected text and briefly explain errors found."
                    },
                    {"role": "user", "content": f"Check this {lang_name} text for grammar errors:\n\n{text}"},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            result = response.choices[0].message.content.strip()
            return {
                'success': True,
                'result': result,
                'original': text,
                'provider': 'openai'
            }
        except Exception as e:
            last_err = str(e)
    else:
        last_err = None

    # Free fallback: LanguageTool public API
    try:
        # Map language
        lang_code = 'en-US' if language.lower().startswith('en') else 'vi-VN'
        resp = requests.post(
            'https://api.languagetool.org/v2/check',
            data={
                'text': text,
                'language': lang_code,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        matches: List[Dict[str, Any]] = data.get('matches', [])

        # Build corrected text by applying first replacement of each match
        corrected = text
        # Apply from end to start to keep offsets valid
        def _first_replacement(m):
            reps = m.get('replacements', [])
            return reps[0]['value'] if reps else None

        # Sort by offset desc
        for m in sorted(matches, key=lambda x: x.get('offset', 0), reverse=True):
            off = m.get('offset', 0)
            length = m.get('length', 0)
            rep = _first_replacement(m)
            if rep is None:
                continue
            try:
                corrected = corrected[:off] + rep + corrected[off+length:]
            except Exception:
                # Ignore malformed offsets
                pass

        # Build readable issues list
        issues_lines = []
        for m in matches:
            msg = m.get('message', '')
            rule = m.get('rule', {}).get('id', '')
            repl = _first_replacement(m)
            if repl:
                issues_lines.append(f"- {msg} → Suggestion: {repl} ({rule})")
            else:
                issues_lines.append(f"- {msg} ({rule})")

        combined = "Corrected:\n" + corrected
        if issues_lines:
            combined += "\n\nIssues:\n" + "\n".join(issues_lines)

        return {
            'success': True,
            'result': combined,
            'original': text,
            'provider': 'languagetool'
        }
    except Exception as e:
        last_err = str(e)

    return {
        'success': False,
        'error': last_err or 'No grammar provider available (OpenAI or LanguageTool)'
    }

async def generate_example(word: str, pos: str = None, definition: str = None) -> Dict[str, Any]:
    """
    Generate example sentence for a vocabulary word
    
    Args:
        word: The vocabulary word
        pos: Part of speech (optional)
        definition: Word definition (optional)
    
    Returns:
        Dict with 'example' and 'success' keys
    """
    if _has_openai():
        try:
            context = f"Word: {word}"
            if pos:
                context += f"\nPart of speech: {pos}"
            if definition:
                context += f"\nDefinition: {definition}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an English teacher. Generate a clear, natural example sentence using the given word. Keep it simple and practical."
                    },
                    {"role": "user", "content": context},
                ],
                temperature=0.7,
                max_tokens=100,
            )
            example = response.choices[0].message.content.strip().strip('"').strip("'")
            return {
                'success': True,
                'example': example,
                'word': word,
                'provider': 'openai'
            }
        except Exception:
            pass
    # Free fallback: simple template-based sentence
    templates = [
        f"I use the word '{word}' in a sentence.",
        f"This {pos or 'word'} '{word}' is easy to remember.",
        f"Can you explain the meaning of '{word}'?",
        f"She often says '{word}' in daily conversations.",
        f"Learning '{word}' helps me improve my English."
    ]
    # Pick the first deterministic template (no randomness to keep deterministic tests)
    return {
        'success': True,
        'example': templates[0],
        'word': word,
        'provider': 'template'
    }

async def suggest_synonyms(word: str, pos: str = None, language: str = 'en', translate_to: Optional[str] = 'vi') -> Dict[str, Any]:
    """
    Suggest synonyms for a word
    
    Args:
        word: The vocabulary word
        pos: Part of speech (optional)
    
    Returns:
        Dict with 'synonyms' list and 'success' keys
    """
    if _has_openai():
        try:
            context = f"Word: {word}"
            if pos:
                context += f"\nPart of speech: {pos}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an English vocabulary expert. Provide 5 common synonyms for the given word. List them separated by commas, no explanations."
                    },
                    {"role": "user", "content": context},
                ],
                temperature=0.5,
                max_tokens=100,
            )
            synonyms_text = response.choices[0].message.content.strip()
            synonyms = [s.strip() for s in synonyms_text.split(',')]
            syn = synonyms[:5]
            result: Dict[str, Any] = {
                'success': True,
                'provider': 'openai',
                'word': word,
                'language': language,
            }
            if language.startswith('vi') and translate_to:
                # Word is Vietnamese -> translate to EN to align with OpenAI
                # But since we already asked in EN, just return EN list and a VI translation list
                vi_syn = _translate_list(syn, 'en', 'vi')
                result['synonyms'] = [{'en': e, 'vi': v} for e, v in zip(syn, vi_syn)]
            elif language.startswith('en') and (translate_to and translate_to.startswith('vi')):
                vi_syn = _translate_list(syn, 'en', 'vi')
                result['synonyms'] = [{'en': e, 'vi': v} for e, v in zip(syn, vi_syn)]
            else:
                result['synonyms'] = [{'en': e} for e in syn]
            return result
        except Exception:
            pass

    # Free fallback: Datamuse API (public)
    try:
        params = {"ml": word}
        # Try direct synonyms list as well
        r = requests.get("https://api.datamuse.com/words", params=params, timeout=10)
        r.raise_for_status()
        items = r.json()
        # If language is vi, translate headword to en first to improve results
        en_head = word
        if language.startswith('vi'):
            en_head = _translate_mymemory(word, 'vi', 'en') or word
            r2 = requests.get("https://api.datamuse.com/words", params={"ml": en_head}, timeout=10)
            if r2.ok:
                items = r2.json()

        synonyms = [it.get('word') for it in items if it.get('word')]
        syn = synonyms[:5]
        result: Dict[str, Any] = {
            'success': True,
            'provider': 'datamuse',
            'word': word,
            'language': language,
        }
        if language.startswith('en') and translate_to and translate_to.startswith('vi'):
            vi_syn = _translate_list(syn, 'en', 'vi')
            result['synonyms'] = [{'en': e, 'vi': v} for e, v in zip(syn, vi_syn)]
        elif language.startswith('vi'):
            # We looked up via EN; translate back to VI
            vi_syn = _translate_list(syn, 'en', 'vi')
            result['synonyms'] = [{'en': e, 'vi': v} for e, v in zip(syn, vi_syn)]
        else:
            result['synonyms'] = [{'en': e} for e in syn]
        return result
    except Exception:
        pass

    return {
        'success': False,
        'error': 'No synonym provider available'
    }


async def suggest_antonyms(word: str, pos: str = None, language: str = 'en', translate_to: Optional[str] = 'vi') -> Dict[str, Any]:
    """
    Suggest antonyms for a word with optional bilingual output.
    """
    # Prefer OpenAI
    if _has_openai():
        try:
            context = f"Word: {word}"
            if pos:
                context += f"\nPart of speech: {pos}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an English vocabulary expert. Provide 5 common antonyms for the given word. List them separated by commas, no explanations."
                    },
                    {"role": "user", "content": context},
                ],
                temperature=0.5,
                max_tokens=100,
            )
            antonyms_text = response.choices[0].message.content.strip()
            ants = [s.strip() for s in antonyms_text.split(',')][:5]
            result: Dict[str, Any] = {
                'success': True,
                'provider': 'openai',
                'word': word,
                'language': language,
            }
            if language.startswith('en') and translate_to and translate_to.startswith('vi'):
                vi_ants = _translate_list(ants, 'en', 'vi')
                result['antonyms'] = [{'en': e, 'vi': v} for e, v in zip(ants, vi_ants)]
            elif language.startswith('vi'):
                vi_ants = _translate_list(ants, 'en', 'vi')
                result['antonyms'] = [{'en': e, 'vi': v} for e, v in zip(ants, vi_ants)]
            else:
                result['antonyms'] = [{'en': e} for e in ants]
            return result
        except Exception:
            pass

    # Free fallback: Datamuse antonyms
    try:
        # For better results in VI, translate headword to EN
        en_head = word
        if language.startswith('vi'):
            en_head = _translate_mymemory(word, 'vi', 'en') or word
        r = requests.get("https://api.datamuse.com/words", params={"rel_ant": en_head}, timeout=10)
        r.raise_for_status()
        items = r.json()
        ants = [it.get('word') for it in items if it.get('word')][:5]
        result: Dict[str, Any] = {
            'success': True,
            'provider': 'datamuse',
            'word': word,
            'language': language,
        }
        if language.startswith('en') and translate_to and translate_to.startswith('vi'):
            vi_ants = _translate_list(ants, 'en', 'vi')
            result['antonyms'] = [{'en': e, 'vi': v} for e, v in zip(ants, vi_ants)]
        elif language.startswith('vi'):
            vi_ants = _translate_list(ants, 'en', 'vi')
            result['antonyms'] = [{'en': e, 'vi': v} for e, v in zip(ants, vi_ants)]
        else:
            result['antonyms'] = [{'en': e} for e in ants]
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}
