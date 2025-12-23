# app/services/handwriting_engine/segmenter_docufcn.py
from collections import OrderedDict
import torch
import torch.nn.functional as F
from torch import nn

class DocUFCN(nn.Module):
    def __init__(self, num_classes: int = 3, input_channels: int = 3,
                 encoder_dropout_prob: float = 0.0, decoder_dropout_prob: float = 0.0):
        super().__init__()
        self.num_classes = num_classes
        self.num_input_channels = input_channels
        self.feature_sizes = [32, 64, 128, 256]

        self.encoder_blocks = self._build_encoder(input_channels, encoder_dropout_prob)
        self.decoder_blocks = self._build_decoder(decoder_dropout_prob)
        self.classifier = nn.Conv2d(2 * self.feature_sizes[0], num_classes, kernel_size=3, padding=1)

    def _conv_layer(self, in_c, out_c, dropout, dilation=1, conv_class=nn.Conv2d,
                    kernel_size=3, stride=1, padding=1):
        layers = OrderedDict({
            "conv": conv_class(in_c, out_c, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation),
            "bn": nn.BatchNorm2d(out_c),
            "relu": nn.ReLU(),
        })
        if dropout and dropout > 0:
            layers["dropout"] = nn.Dropout(dropout)
        return nn.Sequential(layers)

    def _calc_padding(self, in_size, out_size, kernel_size, stride, dilation):
        return int(-(in_size - kernel_size - (kernel_size - 1) * (dilation - 1) - (out_size - 1) * stride) / 2)

    def _build_encoder_conv_block(self, in_c, out_c, dropout):
        convs = [self._conv_layer(in_c, out_c, dropout, dilation=1)]
        for d in [2, 4, 8, 16]:
            pad = self._calc_padding(out_c, out_c, 3, 1, d)
            convs.append(self._conv_layer(out_c, out_c, dropout, dilation=d, padding=pad))
        return nn.Sequential(*convs)

    def _build_encoder(self, input_channels, dropout):
        sizes = [input_channels] + self.feature_sizes
        return nn.ModuleList([self._build_encoder_conv_block(a, b, dropout) for a, b in zip(sizes, sizes[1:])])

    def _build_decoder_conv_block(self, in_c, out_c, dropout):
        return nn.Sequential(OrderedDict({
            "conv": self._conv_layer(in_c, out_c, dropout),
            "upsample": self._conv_layer(out_c, out_c, dropout, kernel_size=2, stride=2, padding=0, conv_class=nn.ConvTranspose2d)
        }))

    def _build_decoder(self, dropout):
        fs = list(reversed(self.feature_sizes))
        blocks = [self._build_decoder_conv_block(fs[0], fs[1], dropout)]
        for a, b in zip(fs[1:], fs[2:]):
            blocks.append(self._build_decoder_conv_block(2 * a, b, dropout))
        return nn.ModuleList(blocks)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        block_results = []
        h = self.encoder_blocks[0](x)
        for enc in self.encoder_blocks[1:]:
            block_results.append(h.clone())
            h = F.max_pool2d(h, 2, stride=2)
            h = enc(h)

        for dec, skip in zip(self.decoder_blocks, reversed(block_results)):
            h = dec(h)
            h = torch.cat([h, skip], dim=1)

        return self.classifier(h)

    @torch.no_grad()
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.forward(x)
        return torch.softmax(logits, dim=1)
