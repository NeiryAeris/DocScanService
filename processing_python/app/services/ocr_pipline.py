# app/services/ocr_pipeline.py

from typing import List, Dict, Any
import base64
import io

from PIL import Image
import pytesseract
from pytesseract import Output

from app.core.ocr_text_utils import normalize_text, tokenize_basic, BoxTuple


def run_ocr_image_bytes(
    image_bytes: bytes,
    languages: List[str],
) -> Dict[str, Any]:
    """
    OCR pipeline:
      - bytes -> image
      - Tesseract -> words + boxes
      - normalize_text + tokenize_basic from docsearch_cli
    """

    # 1) Load image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 2) Language string (like 'vie+eng')
    lang_arg = "+".join(languages) if languages else "vie+eng"

    # 3) Tesseract with detailed data (like your TSV)
    data = pytesseract.image_to_data(
        img,
        lang=lang_arg,
        output_type=Output.DICT,
        # TODO: later: add PSM/OEM from req.options if you want
        # config="--psm 6 --oem 1"
    )

    # 4) Build raw words + boxes
    boxes = []
    words = []
    idx = 0
    n = len(data["text"])

    for i in range(n):
        text = (data["text"][i] or "").strip()
        conf_str = data["conf"][i]
        try:
            conf = float(conf_str) if conf_str not in (None, "", "-1") else -1.0
        except Exception:
            conf = -1.0

        if text and conf >= 0:
            left = float(data["left"][i] or 0)
            top = float(data["top"][i] or 0)
            w = float(data["width"][i] or 0)
            h = float(data["height"][i] or 0)
            boxes.append((idx, text, conf, left, top, w, h))
            words.append(text)
            idx += 1

    raw_text = " ".join(words)

    # 5) SAME normalization as your CLI
    clean_text = normalize_text(raw_text)

    # 6) SAME tokenization as your CLI
    tokens, positions = tokenize_basic(clean_text)

    main_lang = languages[0] if languages else "vie+eng"

    return {
        "text": clean_text,
        "language": main_lang,
        "tokens": tokens,
        "tokenPositions": positions,
        "boxes": [
            {
                "tokenIndex": i,
                "text": txt,
                "conf": conf,
                "x": left,
                "y": top,
                "w": w,
                "h": h,
            }
            for (i, txt, conf, left, top, w, h) in boxes
        ],
    }


def run_ocr_image_base64(
    image_base64: str,
    languages: List[str],
) -> Dict[str, Any]:
    img_bytes = base64.b64decode(image_base64)
    return run_ocr_image_bytes(img_bytes, languages)
