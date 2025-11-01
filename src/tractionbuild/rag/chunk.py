from __future__ import annotations
import hashlib
import unicodedata
from typing import List
from pydantic import BaseModel

class Chunk(BaseModel):
    id: str
    text: str
    start: int
    end: int
    sha1: str

def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip()

def split_structural(text: str) -> List[str]:
    # A simple implementation, can be improved with more sophisticated rules
    return [p.strip() for p in text.split("\n\n") if p.strip()]

def reflow(paragraphs: List[str], tokens_per_chunk: int = 400, overlap: int = 60) -> List[Chunk]:

    # 1) Build primary chunks by word-count

    primaries: List[str] = []

    cur = []

    for para in paragraphs:

        words = para.split()

        if len(" ".join(cur + words).split()) > tokens_per_chunk and cur:

            primaries.append(" ".join(cur))

            cur = words

        else:

            cur += ([ "\n\n"] if cur else []) + words

    if cur:

        primaries.append(" ".join(cur))



    # 2) Add forward overlap (does not change boundaries, just duplicated tokens)

    final_texts: List[str] = []

    for i, base in enumerate(primaries):

        if i < len(primaries) - 1 and overlap > 0:

            nxt = " ".join(primaries[i + 1].split()[:overlap])

            final_texts.append(f"{base} {nxt}".strip())

        else:

            final_texts.append(base.strip())



    # 3) Materialize Chunks with SHA after overlap (deterministic IDs)

    chunks: List[Chunk] = []

    for idx, txt in enumerate(final_texts):

        sha1 = hashlib.sha1(txt.encode("utf-8")).hexdigest()

        chunks.append(Chunk(

            id=f"chunk_{idx}_{sha1[:8]}",

            text=txt,

            start=0,   # keep neutral; char spans are optional here

            end=0,

            sha1=sha1

        ))

    return chunks
