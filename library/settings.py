import torch

from typing import Optional


class Settings:
    def __init__(self, name: str, save_path: str, epochs: int = 1, batch_size: int = 32,
                 device: torch.device = torch.device("cpu"), scheduler: str = "exponential", gamma: float = 1.0,
                 verbose: bool = True, report_progress_every: int = 1, main_metric: str = "wer",
                 keep_only_best_checkpoint: bool = True, optimizer: str = "adam", lr: float = 0.001,
                 weight_decay: float = 0.0, grad_clip: Optional[float] = None, embedding_size: int = 64,
                 hidden_size: int = 128, num_layers: int = 1, dropout: float = 0.0, tau: int = 1,
                 loss: str = "cross-entropy", use_features: bool = False, feature_embedding_size: int = 32,
                 feature_hidden_size: int = 128, feature_num_layers: int = 0, feature_pooling: str = "mean") -> None:
        # Experiment settings
        self.name = name
        self.save_path = save_path

        # Training settings
        self.loss = loss
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = device
        self.verbose = verbose
        self.report_progress_every = report_progress_every
        self.main_metric = main_metric
        self.keep_only_best_checkpoint = keep_only_best_checkpoint

        # Optimizer settings
        self.scheduler = scheduler
        self.gamma = gamma
        self.optimizer = optimizer
        self.lr = lr
        self.weight_decay = weight_decay
        self.grad_clip = grad_clip

        # Model Settings
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.tau = tau
        self.use_features = use_features
        self.feature_embedding_size = feature_embedding_size
        self.feature_hidden_size = feature_hidden_size
        self.feature_num_layers = feature_num_layers
        self.feature_pooling = feature_pooling
