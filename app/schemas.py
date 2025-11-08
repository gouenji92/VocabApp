from pydantic import BaseModel
from typing import Optional, List, Dict

class VocabSet(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    language_from: str = 'en'
    language_to: str = 'vi'
    user_id: Optional[str] = None
    visibility: str = 'private'  # 'private' or 'public'
    owner_username: Optional[str] = None
    created_at: Optional[str] = None

class VocabTerm(BaseModel):
    id: str
    set_id: str
    term: str
    definition: str
    pos: Optional[str] = None
    example: Optional[str] = None

class ImportPreview(BaseModel):
    mapping: Dict[str, Optional[str]]
    headers: List[str]
    sample: List[Dict[str, str]]
    set_name: str

class ImportResult(BaseModel):
    set_id: str
    inserted: int
    skipped: int
