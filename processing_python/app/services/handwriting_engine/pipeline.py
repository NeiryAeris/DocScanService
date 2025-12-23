# app/services/handwriting_engine/pipeline.py
import base64
import io
import torch
import torch.nn as nn
import httpx
from PIL import Image

from .loader import load_segmenter
from .inpaint_lbam import LBAMInpainter
from .tiling import iter_tiles, stitch_average

class HandwritingRemovalPipeline:
    def __init__(self, device: str, seg_ckpt: str, inpaint_weights: str,
                 patch_size: int = 256, overlap: int = 32, handwriting_class: int = 2):
        self.device = device
        self.patch_size = patch_size
        self.overlap = overlap
        self.handwriting_class = handwriting_class

        self.segmenter = load_segmenter(seg_ckpt, device=self.device)
        self.inpainter = LBAMInpainter(inpaint_weights, device=device)

        self.dilate = nn.MaxPool2d(kernel_size=7, stride=1, padding=3)

    def run_local_file_to_png(self, image_path: str) -> bytes:
        img = Image.open(image_path).convert("RGB")
        x = self._pil_to_tensor_01(img)  # (3,H,W) in [0..1]
        H, W = x.shape[1], x.shape[2]
        dev = torch.device(self.device)

        # ---- 1) build handwriting mask by tiling segmentation ----
        mask_acc = torch.zeros((1, H, W), device=dev)

        for x0, y0, x1, y1 in iter_tiles(W, H, self.patch_size, self.overlap):
            patch = x[:, y0:y1, x0:x1]
            if patch.shape[1] != self.patch_size or patch.shape[2] != self.patch_size:
                continue

            inp = patch.unsqueeze(0).to(dev)
            proba = self.segmenter.predict_proba(inp)  # (1,C,256,256)
            hw = proba[0, self.handwriting_class:self.handwriting_class+1, :, :]
            mask_acc[:, y0:y1, x0:x1] = torch.maximum(mask_acc[:, y0:y1, x0:x1], hw)

        bin_mask = (mask_acc >= 0.5).float()
        keep_mask = 1.0 - self.dilate(bin_mask.unsqueeze(0)).squeeze(0)  # (1,H,W)

        # ---- 2) inpaint each tile ----
        tiles = []
        for x0, y0, x1, y1 in iter_tiles(W, H, self.patch_size, self.overlap):
            patch = x[:, y0:y1, x0:x1]
            km = keep_mask[:, y0:y1, x0:x1]
            if patch.shape[1] != self.patch_size or patch.shape[2] != self.patch_size:
                continue

            out_patch = self.inpainter.inpaint(patch.to(dev), km.to(dev))
            tiles.append((x0, y0, x1, y1, out_patch))

        merged = stitch_average(W, H, self.patch_size, tiles, dev)
        return self._tensor_to_png_bytes(merged)

    def run_local_file_to_data_url(self, image_path: str) -> str:
        png = self.run_local_file_to_png(image_path)
        b64 = base64.b64encode(png).decode("utf-8")
        return f"data:image/png;base64,{b64}"


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
        x = self._pil_to_tensor_01(img)  # (3,H,W)
        H, W = x.shape[1], x.shape[2]
        dev = torch.device(self.device)

        # ---- 1) build handwriting mask by tiling segmentation ----
        mask_acc = torch.zeros((1, H, W), device=dev)

        for x0, y0, x1, y1 in iter_tiles(W, H, self.patch_size, self.overlap):
            patch = x[:, y0:y1, x0:x1]
            if patch.shape[1] != self.patch_size or patch.shape[2] != self.patch_size:
                continue

            inp = patch.unsqueeze(0).to(dev)
            proba = self.segmenter.predict_proba(inp)  # (1,C,256,256)
            hw = proba[0, self.handwriting_class:self.handwriting_class+1, :, :]  # (1,256,256)
            mask_acc[:, y0:y1, x0:x1] = torch.maximum(mask_acc[:, y0:y1, x0:x1], hw)

        # threshold + dilate a bit (same idea as WPI)
        bin_mask = (mask_acc >= 0.5).float()
        # invert for keep-mask: 1=keep, 0=hole
        keep_mask = 1.0 - self.dilate(bin_mask.unsqueeze(0)).squeeze(0)  # (1,H,W)

        # ---- 2) inpaint each tile ----
        tiles = []
        for x0, y0, x1, y1 in iter_tiles(W, H, self.patch_size, self.overlap):
            patch = x[:, y0:y1, x0:x1]
            km = keep_mask[:, y0:y1, x0:x1]
            if patch.shape[1] != self.patch_size or patch.shape[2] != self.patch_size:
                continue

            out_patch = self.inpainter.inpaint(patch.to(dev), km.to(dev))
            tiles.append((x0, y0, x1, y1, out_patch))

        merged = stitch_average(W, H, self.patch_size, tiles, dev)

        png = self._tensor_to_png_bytes(merged)
        b64 = base64.b64encode(png).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    