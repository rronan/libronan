import re

import numpy as np
import torch
import torch.utils.data
from torch._six import container_abcs, int_classes, string_classes


class Dataset(torch.utils.data.Dataset):
    def __init__(self, args, set_):
        self.set_ = set_
        self.count = args.count

    def make_data(self, input_prefix, set_):
        self.data = ""

    def count_data(self, c=-1):
        self.n_videos, self.n_frames, *_ = self.data.shape
        self.count = self.n_videos * self.n_frames
        self.count = self.count if c < 0 else min(self.count, c)

    def print_stats(self):
        d = {"input": self.data}
        print("*****", self.set_, sep="\n")
        for key, value in d.items():
            print(f"{key} max :", np.max(value))
            print(f"{key} min :", np.min(value))
            print(f"{key} mean :", np.mean(value))
            print(f"{key} std :", np.std(value))
            print(f"{key} shape :", value.shape)
        print(f"n samples {self.set_}: {self.count}")

    def get_input(self, video_idx, frame_idx):
        pass

    def get_target(self, video_idx, frame_idx):
        pass

    def getitem(self, video_idx, frame_idx):
        input_ = self.get_input(video_idx, frame_idx)
        target = self.get_target(video_idx, frame_idx)
        return input_, target

    def __getitem__(self, index):
        video_idx = index // self.n_frames
        frame_idx = index % self.n_frames
        return self.getitem(video_idx, frame_idx)

    def __len__(self):
        return self.count


np_str_obj_array_pattern = re.compile(r"[SaUO]")


def cat_collate(batch):
    elem = batch[0]
    elem_type = type(elem)
    if isinstance(elem, torch.Tensor):
        numel = sum([x.numel() for x in batch])
        storage = elem.storage()._new_shared(numel)
        out = elem.new(storage)
        return torch.cat(batch, 0, out=out)
    elif (
        elem_type.__module__ == "numpy"
        and elem_type.__name__ != "str_"
        and elem_type.__name__ != "string_"
    ):
        elem = batch[0]
        if elem_type.__name__ == "ndarray":
            if np_str_obj_array_pattern.search(elem.dtype.str) is not None:
                raise TypeError("default_collate_err_msg_format", elem.dtype)
            return cat_collate([torch.as_tensor(b) for b in batch])
        elif elem.shape == ():  # scalars
            return torch.as_tensor(batch)
    elif isinstance(elem, float):
        return torch.tensor(batch, dtype=torch.float64)
    elif isinstance(elem, int_classes):
        return torch.tensor(batch)
    elif isinstance(elem, string_classes):
        return batch
    elif isinstance(elem, container_abcs.Mapping):
        return {key: cat_collate([d[key] for d in batch]) for key in elem}
    elif isinstance(elem, tuple) and hasattr(elem, "_fields"):  # namedtuple
        return elem_type(*(cat_collate(samples) for samples in zip(*batch)))
    elif isinstance(elem, container_abcs.Sequence):
        transposed = zip(*batch)
        return [cat_collate(samples) for samples in transposed]

    raise TypeError("default_collate_err_msg_format", elem_type)
