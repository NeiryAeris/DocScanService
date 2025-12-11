# app/services/ocr_pipeline/preprocess.py

from typing import Any
from PIL import Image
import io


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """
    Load a PIL Image from raw bytes.
    """
    return Image.open(io.BytesIO(image_bytes))


def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Apply your preprocessing pipeline.

    This is where you plug in:
      - resizing
      - grayscale
      - binarization
      - denoising
      - deskew
      - etc.

    For now it's a simple placeholder.
    """
    # Example: convert to grayscale
    img = img.convert("L")

    # TODO: copy your real preprocessing steps from the CLI here.

    return img
