import torch
import torch.nn.functional as F
from torch import nn

from .trans_u_net.vit_seg_modeling import VisionTransformer, VIT_CONFIGS

class TransUNetWrapper(nn.Module):
    def __init__(self, img_size: int, num_classes: int = 3, pretrained_model_name: str = "R50-ViT-B_16",
                 num_skip_channels: int = 3, vit_patch_size: int = 16):
        super().__init__()
        cfg = VIT_CONFIGS[pretrained_model_name]
        cfg.n_classes = num_classes
        cfg.n_skip = num_skip_channels
        cfg.patches.grid = (img_size // vit_patch_size, img_size // vit_patch_size)

        self.net = VisionTransformer(cfg, img_size=img_size, num_classes=num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    @torch.no_grad()
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.forward(x)
        return torch.softmax(logits, dim=1)
