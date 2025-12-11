import re
import unicodedata
from typing import List, Tuple

# (idx, text, conf, left, top, width, height)
BoxTuple = Tuple[int, str, float, float, float, float, float]

def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"-\s*\n\s*", "", s)                 # join hyphenation across line breaks
    s = s.replace("\r", " ").replace("\n", " ")
    s = re.sub(r"[ \t\f\v]+", " ", s).strip()
    return s

def tokenize_basic(s: str) -> Tuple[List[str], List[int]]:
    tokens: List[str] = []
    positions: List[int] = []
    pos = 0
    word: List[str] = []

    for ch in s:
        if re.match(r"[0-9A-Za-zÀ-ỹ_\-]", ch):
            word.append(ch)
        else:
            if word:
                tokens.append("".join(word).lower())
                pos += 1
                positions.append(pos)
                word = []

    if word:
        tokens.append("".join(word).lower())
        pos += 1
        positions.append(pos)

    return tokens, positions