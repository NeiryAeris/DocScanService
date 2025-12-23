# app/services/handwriting_engine/tiling.py
import math
import torch

def iter_tiles(w: int, h: int, tile: int, overlap: int):
    step = tile - overlap
    nx = max(1, math.ceil((w - overlap) / step))
    ny = max(1, math.ceil((h - overlap) / step))
    for yi in range(ny):
        y0 = min(yi * step, h - tile)
        y0 = max(0, y0)
        for xi in range(nx):
            x0 = min(xi * step, w - tile)
            x0 = max(0, x0)
            yield x0, y0, x0 + tile, y0 + tile

def stitch_average(out_w: int, out_h: int, tile: int, tiles, device):
    acc = torch.zeros((3, out_h, out_w), device=device)
    wgt = torch.zeros((1, out_h, out_w), device=device)
    for (x0, y0, x1, y1, patch) in tiles:
        acc[:, y0:y1, x0:x1] += patch
        wgt[:, y0:y1, x0:x1] += 1.0
    return acc / torch.clamp(wgt, min=1.0)
