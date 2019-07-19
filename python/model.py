from collections import OrderedDict

import torch
import torch.optim as optim
from torch import nn
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torchviz import make_dot, make_dot_from_trace


class Model(object):
    def __init__(self):
        super().__init__()
        __name__ = "model"
        self.is_gpu = False
        self.is_data_parallel = False

    def set_optim(self, args):
        self.grad_clip = args.grad_clip
        self.optimizer = vars(optim)[args.optimizer](
            self.core_module.parameters(), lr=args.lr, weight_decay=args.weight_decay
        )
        self.scheduler = ReduceLROnPlateau(
            self.optimizer,
            patience=args.lr_patience,
            factor=args.lr_decay,
            verbose=True,
            eps=1e-9,
        )

    def update(self, loss):
        self.core_module.zero_grad()
        loss.backward()
        if self.grad_clip:
            clip_grad_norm_(self.core_module.parameters, self.grad_clip)
        self.optimizer.step()

    def step(self, batch, set_):
        x, y = batch[0], batch[1]
        if self.is_gpu:
            x = x.cuda()
            y = y.cuda()
        pred = self.core_module(x)
        loss = self.loss.forward(pred, y)
        if set_ == "train":
            self.update(loss)
        return {"loss": loss.data.item()}

    def load(self, path):
        print(f"loading {path}")
        state_dict = torch.load(path, map_location=lambda storage, loc: storage)
        try:
            self.core_module.load_state_dict(state_dict)
        except RuntimeError as e:
            print(e)
            state_dict = OrderedDict(
                {k.replace("module.", "", 1): v for k, v in state_dict.items()}
            )
            self.core_module.load_state_dict(state_dict)

    def save(self, path, epoch):
        with open(path / f"{self.__name__}.txt", "w") as f:
            f.write(str(self))
        if self.is_data_parallel:
            state_dict = self.core_module.module.state_dict()
        else:
            state_dict = self.core_module.state_dict()
        torch.save(state_dict, path / f"weights_{epoch}.pth")

    def gpu(self):
        self.core_module.cuda()
        self.is_gpu = True

    def data_parallel(self):
        self.core_module = nn.DataParallel(self.core_module)
        self.is_data_parallel = True

    def get_lr(self):
        return self.optimizer.param_groups[0]["lr"]

    def get_num_parameters(self):
        return sum([m.numel() for m in self.core_module.parameters()])

    def make_dot(self, *x):
        if self.is_gpu:
            x = [xx.cuda() for xx in x]
        dot = make_dot(self(*x), params=dict(self.core_module.named_parameters()))
        dot.render("dot", view=False)

    def make_dot_from_trace(self, *x):
        if self.is_gpu:
            x = [xx.cuda() for xx in x]
        with torch.onnx.set_training(self.core_module, False):
            trace, _ = torch.jit.get_trace_graph(self.core_module, args=(*x,))
        dot = make_dot_from_trace(trace)
        dot.render("dot_from_trace", view=False)

    def output(self):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return self.core_module.forward(*args, **kwargs)
