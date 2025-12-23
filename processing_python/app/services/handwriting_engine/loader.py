# app/services/handwriting_engine/loader.py
from pathlib import Path
import torch
import pickle
import pathlib
from . import pickle_compat

from .segmenter_docufcn import DocUFCN
from .segmenter_transunet import TransUNetWrapper

def torch_load_ckpt(path: str):
    # Try safe load first (torch>=2.6 defaults weights_only=True)
    try:
        return torch.load(path, map_location="cpu")
    except Exception as e:
        msg = str(e)

        # If it's the safe-unpickler complaining about PosixPath, try allowlisting.
        if "Weights only load failed" in msg and "pathlib.PosixPath" in msg:
            try:
                with torch.serialization.safe_globals([pathlib.PosixPath, pathlib.WindowsPath, pathlib.Path]):
                    return torch.load(path, map_location="cpu")
            except Exception:
                pass

        # If full pickle fails on Windows due to PosixPath instantiation, use pickle_compat.
        if "cannot instantiate 'PosixPath'" in msg or "PosixPath" in msg:
            return torch.load(path, map_location="cpu", weights_only=False, pickle_module=pickle_compat)

        # Last resort (trusted ckpt): also use pickle_compat to be safe cross-platform
        return torch.load(path, map_location="cpu", weights_only=False, pickle_module=pickle_compat)


def _resolve_path(p: str) -> str:
    path = Path(p)
    if path.is_file():
        return str(path)
    # try relative to project root (processing_python/)
    root = Path(__file__).resolve().parents[4]
    cand = (root / p.lstrip("/\\")).resolve()
    return str(cand)

def load_segmenter(ckpt_path: str, device: str):
    ckpt_path = _resolve_path(ckpt_path)
    blob = torch_load_ckpt(ckpt_path)
    
    # Heuristic: TransUNet ckpts usually contain transformer/embeddings keys
    state_dict = blob.get("state_dict", blob) if isinstance(blob, dict) else blob
    keys = list(state_dict.keys()) if isinstance(state_dict, dict) else []
    is_transunet = ("trans_u_net" in ckpt_path.lower()) or any("transformer.embeddings" in k for k in keys)

    if is_transunet:
        # match WPI config defaults
        model = TransUNetWrapper(img_size=224, num_classes=3, pretrained_model_name="R50-ViT-B_16",
                                 num_skip_channels=3, vit_patch_size=16)

        # strip lightning prefix if needed
        cleaned = {}
        for k, v in state_dict.items():
            k2 = k
            if k2.startswith("segmentation_network."):
                k2 = k2.replace("segmentation_network.", "", 1)
            if k2.startswith("net."):
                k2 = k2.replace("net.", "", 1)
            cleaned[k2] = v

        model.load_state_dict(cleaned, strict=False)
        model.eval().to(torch.device(device))
        return model

    # fallback: DocUFCN
    model = DocUFCN(num_classes=3, input_channels=3)
    model.load_state_dict(state_dict, strict=False)
    model.eval().to(torch.device(device))
    return model
