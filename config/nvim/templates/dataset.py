#!/usr/bin/env python3

import torch.utils.data

class Dataset(torch.utils.data.Dataset):

    def __init__(self, args, set_):
        self.set_ = set_

    def count_data(self, c=None):
        self.count =
        self.count = self.count if c is None else min(self.count, c)

    def print_stats(self):
        pass

    def get_input(self, video_idx, frame_idx):
        pass

    def get_target(self, video_idx, frame_idx):
        pass

    def __getitem__(self, index):
        video_idx = index // self.n_frames
        frame_idx = index % self.n_frames

    def __len__(self):
        return self.count
