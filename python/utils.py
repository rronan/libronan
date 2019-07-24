import argparse
import hashlib
import json
import math
import random
import re
import time
from copy import copy
from io import BytesIO
from itertools import cycle

import numpy as np
import torch
from PIL import Image
from pygame.color import THECOLORS

COLOR_LIST = [
    list(THECOLORS[x])[:3]
    for x in [
        "red",
        "yellow",
        "blue",
        "cyan",
        "magenta",
        "green",
        "gray",
        "purple",
        "brown",
        "turquoise",
        "wheat",
    ]
]


def set_seed(seed, gpu):
    random.seed(seed)
    torch.manual_seed(seed)
    if gpu:
        torch.cuda.manual_seed_all(seed)


def parse_slice(s):
    a_list = []
    for a in s.split(":"):
        try:
            a_list.append(int(a))
        except ValueError:
            a_list.append(None)
    while len(a_list) < 3:
        a_list.append(None)
    return slice(*a_list)


def write_slice(s):
    return f"{s.start if s.start is not None else ''}:{s.stop if s.stop is not None else ''}"


def write_namespace(s):
    out = []
    for k, v in vars(s).items():
        if type(v) is not bool or v:
            out.append("--" + k)
            if type(v) is bool:
                out.append('""')
            elif type(v) is slice:
                out.append(write_slice(v))
            else:
                out.append(str(v))
    return " ".join(out)


class to_namespace:
    def __init__(self, d):
        vars(self).update(dict([(key, value) for key, value in d.items()]))

    def __str__(self):
        return str(vars(self))


def append_timestamp(name):
    if re.search("'[\d]{4}_[\d]{4}'", name):
        append = ""
    else:
        append = "_" + time.strftime("%y%m%d_%H%M%S")
    return name + append


def save_args(path, args, zf=None):
    args_copy = copy(args)
    for k, v in vars(args_copy).items():
        if type(v) is slice:
            vars(args_copy)[k] = write_slice(v)
        elif type(v) is argparse.Namespace:
            vars(args_copy)[k] = write_namespace(v)
    if zf is None:
        with open(path, "w") as f:
            json.dump(vars(args_copy), f, indent=4, sort_keys=True)
    else:
        zf.writestr(
            str(path).replace("/", "\\"),
            json.dumps(vars(args_copy), indent=4, sort_keys=True),
        )


def fill_index_select(t_a, dim, i_list, t_b):
    t_list = []
    for i in range(t_a.size(dim)):
        idx = torch.LongTensor([i])
        t = t_b.index_select(dim, idx) if i in i_list else t_a.index_select(dim, idx)
        t_list.append(t)
    return torch.cat(t_list, dim)


def image2mask(arr, color_list=COLOR_LIST):
    res = np.zeros(arr.shape[:2])
    for i, c in enumerate(color_list):
        mask = (arr == np.array(c)[:3]).all(axis=2)
        res += (i + 1) * mask
    return res


def binmask2image(arr, color_list=COLOR_LIST):
    im = np.zeros((arr.shape[1], arr.shape[2], 3))
    for m, c in zip(arr, cycle([[0, 0, 0]] + color_list)):
        im += np.repeat(np.expand_dims(m, axis=-1), 3, axis=-1) * np.array(c)
    return im.astype("uint8")


def mask2image(arr, color_list=COLOR_LIST):
    im = np.zeros((*arr.shape, 3))
    for i, c in enumerate(color_list):
        im += np.repeat(np.expand_dims(arr == (i + 1), axis=-1), 3, axis=-1) * np.array(
            c
        )
    return im.astype("uint8")


def process_multi_channel(arr):
    n_channel, i_channel = np.min(arr.shape), np.argmin(arr.shape)
    if n_channel == 1:
        return arr[i_channel]
    if n_channel == 3:
        return arr.transpose((1, 2, 0)) if i_channel == 0 else arr
    if n_channel != 3:
        if i_channel == 2:
            arr = arr.transpose((2, 0, 1))
        return binmask2image(arr)


def normalize(array):
    u = np.unique(array)
    q1, q3 = np.percentile(u, 25), np.percentile(u, 75)
    array = (array - (q1 + q3) / 2) / (q3 - q1) / 1.7  # 1.7 scales contrast
    array = (array * 255 + 127).clip(0, 255)
    return array


def _array2image(arr, norm=None):
    assert len(arr.shape) in [2, 3]
    if len(arr.shape) == 3:
        arr = process_multi_channel(arr)
    if len(arr.shape) == 2:
        if arr.dtype is not np.dtype("float"):
            arr = mask2image(arr)
    if norm is None:
        if arr.max() > 255 or arr.min() < 0:
            arr = normalize(arr)
    elif norm:
        arr = normalize(arr)
    image = Image.fromarray(arr.astype("uint8")).convert("RGB")
    return image


def array2image(arr, norm=None):
    assert len(arr.shape) in [2, 3, 4]
    if len(arr.shape) != 4:
        return _array2image(arr, norm)
    image_list = [_array2image(a, norm) for a in arr]
    n = math.ceil(math.sqrt(len(arr)))
    array_list = [arr[i : i + n] for i in range(0, len(arr), n)]
    array_list = [np.concatenate(a, axis=2) for a in array_list]
    p = array_list[0].shape[-1] - array_list[-1].shape[-1]
    array_list[-1] = np.pad(array_list[-1], ((0, 0), (0, 0), (0, p)), "minimum")
    return _array2image(np.concatenate(array_list, axis=1), norm)


def tensor2image(tensor, normalize=None):
    array = tensor.clone().detach().cpu().numpy()
    image = array2image(array, normalize)
    return image


def to_image_server(im):
    byteimage = BytesIO()
    try:
        im.save(byteimage, format="PNG", compress=1)
    except AttributeError:
        im.savefig(byteimage)
    im_hash = hashlib.sha256(im.tobytes()).hexdigest()
    name = f"/meleze/data0/public_html/rriochet/image_server/{im_hash}.png"
    im.save(name)
    print(
        f"https://www.rocq.inria.fr/cluster-willow/rriochet/image_server/{im_hash}.png"
    )


def tis(x, normalize=None):
    if type(x) is torch.Tensor:
        im = tensor2image(x, normalize)
    elif type(x) is np.ndarray:
        im = array2image(x, normalize)
    elif type(x) is Image.Image:
        im = x
    else:
        raise ValueError
    to_image_server(im)
    return im
