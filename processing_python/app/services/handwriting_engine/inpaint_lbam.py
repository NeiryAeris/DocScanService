# app/services/handwriting_engine/inpaint_lbam.py
import torch
import torch.nn as nn

from .lbam_models.LBAMModel import LBAMModel

class LBAMInpainter:
    def __init__(self, weights_path: str, device: str):
        self.device = torch.device(device)
        self.net = LBAMModel(4, 3)
        state = torch.load(weights_path, map_location="cpu")
        self.net.load_state_dict(state)
        self.net.eval()
        self.net.to(self.device)

        for p in self.net.parameters():
            p.requires_grad = False

    @torch.no_grad()
    def inpaint(self, rgb_patch_01: torch.Tensor, keep_mask_01: torch.Tensor) -> torch.Tensor:
        """
        rgb_patch_01: (3,H,W) float32 in [0..1]
        keep_mask_01: (1,H,W) float32 where 1=keep, 0=hole
        returns: (3,H,W) float32 in [0..1]
        """
        # LBAM expects: input_image = [rgb * keep_mask, hole_mask] where hole_mask is 1 for holes
        hole_mask = 1.0 - keep_mask_01
        masked_rgb = rgb_patch_01 * keep_mask_01

        inp = torch.cat([masked_rgb, hole_mask], dim=0).unsqueeze(0).to(self.device)     # (1,4,H,W)
        mask = keep_mask_01.unsqueeze(0).repeat(1, 3, 1, 1).to(self.device)              # (1,3,H,W)

        out = self.net(inp, mask)  # (1,3,H,W) in [0..1]
        out = out.squeeze(0)

        # merge: keep original where keep_mask=1
        return out * (1.0 - mask.squeeze(0)) + masked_rgb.to(self.device) * mask.squeeze(0)
