# app/services/ocr_pipeline/__init__.py

from typing import List, Dict, Any
from .preprocess import load_image_from_bytes, preprocess_image
from .engine import run_ocr_engine
from .postprocess import postprocess_text


def run_ocr_bytes(image_bytes: bytes, languages: List[str]) -> Dict[str, Any]:
    """
    Main OCR pipeline entrypoint for the backend.

    - image_bytes: raw bytes of the input image (from base64).
    - languages: list like ["vi", "en"].

    Returns:
        {
          "text": "<recognized text>",
          "language": "<primary language>",
          "layout": <optional layout dict or None>
        }
    """

    # 1) Load image object
    img = load_image_from_bytes(image_bytes)

    # 2) Preprocess (deskew, grayscale, threshold, etc.)
    img_pre = preprocess_image(img)

    # 3) Run OCR engine (Tesseract/EasyOCR/your custom code)
    raw_text = run_ocr_engine(img_pre, languages)

    # 4) Postprocess text (normalize, cleanup)
    text_clean = postprocess_text(raw_text)

    main_lang = languages[0] if languages else "en"

    # TODO: if your old pipeline has layout/blocks, add them here
    layout = None

    return {
        "text": text_clean,
        "language": main_lang,
        "layout": layout,
    }
