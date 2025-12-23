# app/services/handwriting_engine/pipeline.py
import base64
import os
import io
import torch
import torch.nn as nn
import httpx
from PIL import Image
import torch.nn.functional as F

from .loader import load_segmenter
from .inpaint_lbam import LBAMInpainter
from .tiling import iter_tiles, stitch_average


class HandwritingRemovalPipeline:
    def __init__(
        self,
        device: str,
        seg_ckpt: str,
        inpaint_weights: str,
        patch_size: int = 256,
        overlap: int = 32,
        handwriting_class: int = 2,
    ):
        self.device = device
        self.patch_size = patch_size
        self.overlap = overlap
        self.handwriting_class = int(handwriting_class)

        # WPI-style: treat low-confidence seg pixels as background
        self.min_conf = float(os.getenv("HW_MIN_CONF", "0.3"))

        self.segmenter = load_segmenter(seg_ckpt, device=self.device)
        self.inpainter = LBAMInpainter(inpaint_weights, device=device)

        # small dilation to cover pen edges
        self.dilate = nn.MaxPool2d(kernel_size=7, stride=1, padding=3)

    def run_local_file_to_png(self, image_path: str) -> bytes:
        img = Image.open(image_path).convert("RGB")
        x = self._pil_to_tensor_01(img)
        out = self._run_tensor(x)
        return self._tensor_to_png_bytes(out)

    def run_local_file_to_data_url(self, image_path: str) -> str:
        png = self.run_local_file_to_png(image_path)
        b64 = base64.b64encode(png).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    def _run_tensor(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (3,H,W) float32 in [0..1]
        returns: (3,H,W) float32 in [0..1] (same original size)
        """
        H0, W0 = x.shape[1], x.shape[2]
        dev = torch.device(self.device)

        # ---- pad to multiples of patch_size so edges aren't skipped ----
        tile = self.patch_size
        pad_h = (tile - (H0 % tile)) % tile
        pad_w = (tile - (W0 % tile)) % tile
        if pad_h or pad_w:
            x = F.pad(x, (0, pad_w, 0, pad_h), mode="replicate")
        H, W = x.shape[1], x.shape[2]

        # TransUNet uses fixed img_size (usually 224). DocUFCN uses tile size.
        seg_size = getattr(self.segmenter, "img_size", tile)

        # ---- 1) handwriting mask via segmentation ----
        mask_acc = torch.zeros((1, H, W), device=dev)

        for x0, y0, x1, y1 in iter_tiles(W, H, tile, self.overlap):
            patch = x[:, y0:y1, x0:x1]
            if patch.shape[1] != tile or patch.shape[2] != tile:
                continue

            inp = patch.unsqueeze(0).to(dev)  # (1,3,256,256)

            # Resize for TransUNet positional embeddings (224)
            seg_inp = inp
            if seg_size != tile:
                seg_inp = F.interpolate(seg_inp, size=(seg_size, seg_size), mode="bilinear", align_corners=False)

            # ✅ WPI normalization: [0..1] -> [-1..1]
            seg_inp = (seg_inp - 0.5) / 0.5

            # proba: (1,C,seg,seg)
            proba = self.segmenter.predict_proba(seg_inp)

            # ✅ Build mask from argmax class map, not proba>=0.5
            maxp, pred = proba.max(dim=1, keepdim=True)     # (1,1,seg,seg), (1,1,seg,seg)
            pred = pred.clone()
            pred[maxp < self.min_conf] = 0                  # low-conf -> background
            hw = (pred == self.handwriting_class).float()   # (1,1,seg,seg) in {0,1}

            # Upscale mask back to tile size so it aligns with inpaint tiles
            if seg_size != tile:
                hw = F.interpolate(hw, size=(tile, tile), mode="nearest")

            mask_acc[:, y0:y1, x0:x1] = torch.maximum(mask_acc[:, y0:y1, x0:x1], hw[0, 0])

        # mask_acc is already 0/1; keep this for safety
        bin_mask = (mask_acc > 0.5).float()  # (1,H,W)

        # 1=keep, 0=hole
        keep_mask = 1.0 - self.dilate(bin_mask.unsqueeze(0)).squeeze(0)  # (1,H,W)

        # ---- 2) inpaint each tile at 256 ----
        tiles = []
        for x0, y0, x1, y1 in iter_tiles(W, H, tile, self.overlap):
            patch = x[:, y0:y1, x0:x1]
            km = keep_mask[:, y0:y1, x0:x1]
            if patch.shape[1] != tile or patch.shape[2] != tile:
                continue

            out_patch = self.inpainter.inpaint(patch.to(dev), km.to(dev))
            tiles.append((x0, y0, x1, y1, out_patch))

        merged = stitch_average(W, H, tile, tiles, dev)

        # crop back to original size
        merged = merged[:, :H0, :W0]
        return merged

    async def _download(self, url: str) -> Image.Image:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")

    @staticmethod
    def _pil_to_tensor_01(img: Image.Image) -> torch.Tensor:
        import torchvision.transforms.functional as TF
        return TF.to_tensor(img).float()  # (3,H,W) in [0..1]

    @staticmethod
    def _tensor_to_png_bytes(t: torch.Tensor) -> bytes:
        import torchvision.transforms.functional as TF
        t = torch.clamp(t, 0.0, 1.0).cpu()
        img = TF.to_pil_image(t)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def run_to_data_url(self, image_url: str) -> str:
        img = await self._download(image_url)
        x = self._pil_to_tensor_01(img)
        out = self._run_tensor(x)

        png = self._tensor_to_png_bytes(out)
        b64 = base64.b64encode(png).decode("utf-8")
        return f"data:image/png;base64,{b64}"
