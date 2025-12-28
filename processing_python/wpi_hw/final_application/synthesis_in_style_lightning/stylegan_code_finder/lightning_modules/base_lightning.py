from typing import List

import pytorch_lightning as pl
import torch
from networks import load_weights
from torch.optim import Optimizer
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from utils.clamped_cosine import ClampedCosineAnnealingLR
from visualization.segmentation_plotter_lightning import SegmentationPlotter
from networks.trans_u_net.utils import Precision, Recall


class BaseSegmenter(pl.LightningModule):
    def __init__(self, configs: dict):
        super().__init__()
        self.configs = configs
        self.segmentation_network = None
        self._initialize_segmentation_network()

        # IMPORTANT:
        # - If fine_tune points to a Lightning .ckpt, DO NOT load it here.
        #   PyTorch Lightning will restore weights after __init__ when using load_from_checkpoint().
        fine_tune = configs.get("fine_tune", None)
        if fine_tune and (not str(fine_tune).endswith(".ckpt")):
            load_weights(self.segmentation_network, fine_tune, key="segmentation_network")
        self.optimizers = None
        self.iterations_per_epoch = self.get_iterations_per_epoch()

        # Plotter is only needed for training/validation visualization.
        # Avoid failing inference runs if class_to_color_map is relative/missing.
        self.segmentation_plotter = None
        self.num_val_visualization = configs.get("num_val_visualization", 0)

        self.save_hyperparameters()
        self.precision_metric = Precision(configs['num_classes'])
        self.recall_metric = Recall(configs['num_classes'])

    def _initialize_segmentation_network(self):
        raise NotImplementedError

    def training_step(self, batch, batch_idx):
        raise NotImplementedError

    def validation_step(self, batch, batch_idx):
        if self.segmentation_plotter is not None and batch_idx < self.num_val_visualization:
            image_dest = self.segmentation_plotter.run(self.segmentation_network, batch)
            self.logger.log_image(key="samples", images=[image_dest])

    def configure_optimizers(self):
        optimizers = self.optimizers
        schedulers = self.get_scheduler(optimizers)
        return optimizers, schedulers

    def get_scheduler(self, optimizers: List[Optimizer]) -> List:
        if 'cosine_max_update_epoch' in self.configs:
            cosine_end_iteration = self.configs['cosine_max_update_epoch'] * self.iterations_per_epoch
        elif 'cosine_max_update_iter' in self.configs:
            cosine_end_iteration = self.configs['cosine_max_update_iter']
        else:
            cosine_end_iteration = self.configs['epochs']

        schedulers = []
        for optimizer in optimizers:
            if self.configs["warm_restarts"]:
                schedulers.append(CosineAnnealingWarmRestarts(optimizer, cosine_end_iteration,
                                                              eta_min=self.configs['end_lr']))
            else:
                schedulers.append(ClampedCosineAnnealingLR(optimizer, cosine_end_iteration,
                                                           eta_min=self.configs['end_lr']))
        return schedulers

    def get_iterations_per_epoch(self) -> int:
        # Inference-only configs may not include training fields
        num_iter_epoch = self.configs.get("num_iter_epoch", None)
        if num_iter_epoch is None:
            return 1  # safe default for inference

        if "max_iter" in self.configs:
            return min(self.configs["max_iter"], num_iter_epoch)

        return num_iter_epoch


    def log_precision_recall_accuracy(self, prediction: torch.Tensor, ground_truth: torch.Tensor, softmax: bool):
        self.log('val_precision', self.precision_metric(prediction, ground_truth, softmax=softmax))
        self.log('val_recall', self.recall_metric(prediction, ground_truth, softmax=softmax))

    def log_handwriting_precision_recall_accuracy(self, prediction: torch.Tensor, ground_truth: torch.Tensor,
                                                  softmax: bool):
        # This presumes that the handwritten class is always the last
        self.log('val_handwriting_precision', self.precision_metric(prediction, ground_truth, softmax=softmax,
                                                                    handwriting=True))
        self.log('val_handwriting_recall', self.recall_metric(prediction, ground_truth, softmax=softmax,
                                                              handwriting=True))
