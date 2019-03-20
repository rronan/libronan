#!/usr/bin/env python3

import numpy as np
import torch
import torch.nn as nn

from libronan.python.model import Model

class Core_MODEL(nn.Module):
    def __init__(self, args):
        pass

    def forward(self, x):
        pass

class MODEL(Model):
    def __init__(self, args):
        super().__init__()
        self.__name__ = ""
        self.core_module = Core_MODEL(args)
        self.is_gpu = False
        self.loss =
        super().set_optim(args)

    def step(self, batch, set_):
        pass
