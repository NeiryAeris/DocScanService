from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import os
import argparse
from app.services.handwriting_engine.pipeline import HandwritingRemovalPipeline


def resolve_path(p: str) -> Path:
    pp = Path(p)
    if pp.is_absolute():
        return pp
    # resolve relative to where you launched python from? -> use ROOT for consistency
    return (ROOT / pp).resolve()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="Path to local image (jpg/png)")
    ap.add_argument("--out", default=".test/clean.png", help="Output PNG path")
    args = ap.parse_args()

    image_path = resolve_path(args.image)
    out_path = resolve_path(args.out)

    print("CWD :", Path.cwd())
    print("ROOT:", ROOT)
    print("IMG :", image_path)
    print("OUT :", out_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    device = os.getenv("HW_DEVICE", "cpu")
    seg_ckpt = os.getenv("HW_SEGMENTER_CKPT", "")
    inpaint = os.getenv("HW_INPAINT_WEIGHTS", "")
    patch = int(os.getenv("HW_PATCH_SIZE", "256"))
    overlap = int(os.getenv("HW_OVERLAP", "32"))
    hw_class = int(os.getenv("HW_HANDWRITING_CLASS", "2"))

    if not seg_ckpt or not inpaint:
        raise RuntimeError("Set HW_SEGMENTER_CKPT and HW_INPAINT_WEIGHTS in your .env first")

    pipe = HandwritingRemovalPipeline(
        device=device,
        seg_ckpt=seg_ckpt,
        inpaint_weights=inpaint,
        patch_size=patch,
        overlap=overlap,
        handwriting_class=hw_class,
    )

    png = pipe.run_local_file_to_png(str(image_path))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(png)

    print("✅ saved:", out_path)


if __name__ == "__main__":
    main()
