import argparse
from functools import wraps
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
from colour import Color
from PIL import Image

COLOR_LIST = [
    [int(c * 255) for c in Color(name).rgb][:3]
    for name in [
        "yellow",
        "orange",
        "turquoise",
        "blue",
        "firebrick",
        "red",
        "green",
        "gray",
        "magenta",
        "brown",
        "cyan",
        "purple",
        "wheat",
        "lightsalmon",
        "palevioletred",
        "darkkhaki",
        "thistle",
        "darkblue",
        "navy",
        "cornsilk",
        "sandybrown",
        "goldenrod",
        "azure",
        "beige",
        "oldlace",
        "slategray",
        "springgreen",
    ]
]


def mp_cache(mp_dict):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            k = func.__name__
            k += "_".join(map(str, args))
            k += "_".join(map(lambda k, v: f"{k}_{v}", kwargs.items()))
            if k in mp_dict:
                return mp_dict[k]
            res = func(*args, **kwargs)
            mp_dict[k] = res
            return res

        return wrapper

    return decorate


def split_sum(data, split_sections):
    num_segments = len(split_sections)
    segment_ids = sum(([k] * l for k, l in enumerate(split_sections)), [])
    return unsorted_segment_sum(data, segment_ids, num_segments)


def segment_sum(data, segment_ids):
    num_segments = len(torch.unique(segment_ids))
    return unsorted_segment_sum(data, segment_ids, num_segments)


# https://gist.github.com/bbrighttaer/207dc03b178bbd0fef8d1c0c1390d4be


def unsorted_segment_sum(data, segment_ids, num_segments):
    if len(segment_ids.shape) == 1:
        s = torch.prod(torch.tensor(data.shape[1:])).long()
        segment_ids = segment_ids.repeat_interleave(s).view(
            segment_ids.shape[0], *data.shape[1:]
        )
    shape = [num_segments] + list(data.shape[1:])
    tensor = torch.zeros(*shape).scatter_add(0, segment_ids, data.float())
    tensor = tensor.type(data.dtype)
    return tensor


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
    if re.search("[\d]{6}_[\d]{6}", name):
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
    assert t_a.is_cuda == t_b.is_cuda
    t_list = []
    for i in range(t_a.size(dim)):
        idx = torch.LongTensor([i])
        if t_a.is_cuda:
            idx = idx.cuda()
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


def _normalize(array):
    array = array.copy()
    u = np.unique(array)
    q1, q3 = np.percentile(u, 25), np.percentile(u, 75)
    array = (array - (q1 + q3) / 2) / (q3 - q1) / 1.7  # 1.7 scales contrast
    array = (array * 255 + 127).clip(0, 255)
    return array


def _array2image(arr, normalize=None):
    assert len(arr.shape) in [2, 3]
    if len(arr.shape) == 3:
        arr = process_multi_channel(arr)
    if len(arr.shape) == 2:
        if arr.dtype is not np.dtype("float32"):
            arr = mask2image(arr)
    if normalize is None:
        # if arr.max() > 255 or arr.min() < 0:
        arr = _normalize(arr)
    elif normalize:
        arr = normalize(arr)
    image = Image.fromarray(arr.astype("uint8")).convert("RGB")
    return image


def array2image(arr, normalize=None):
    assert len(arr.shape) in [2, 3, 4]
    if len(arr.shape) != 4:
        return _array2image(arr, normalize)
    n = math.ceil(math.sqrt(len(arr)))
    arr = np.pad(
        arr,
        ((0, 0), (0, 0), (5, 5), (5, 5)),
        "constant",
        constant_values=len(COLOR_LIST) - 1,
    )
    array_list = [arr[i : i + n] for i in range(0, len(arr), n)]
    array_list = [np.concatenate(a, axis=2) for a in array_list]
    p = array_list[0].shape[-1] - array_list[-1].shape[-1]
    array_list[-1] = np.pad(array_list[-1], ((0, 0), (0, 0), (0, p)), "minimum")
    return _array2image(np.concatenate(array_list, axis=1), normalize)


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


def ti(x, normalize=None):
    if type(x) is torch.Tensor:
        im = tensor2image(x, normalize)
    elif type(x) is np.ndarray:
        im = array2image(x, normalize)
    elif type(x) is Image.Image:
        im = x
    else:
        raise ValueError
    return im


def tis(x, normalize=None):
    im = ti(x, normalize)
    to_image_server(im)
    return im


def load_from_keras(self, h5_path):
    import h5py

    print("loading weights from %s" % h5_path)
    f = h5py.File(h5_path)
    k = 1
    numel = 0
    for m in self.modules():
        if isinstance(m, nn.Conv2d):
            w = f["model_weights"]["conv2d_%d" % k]["conv2d_%d" % k]
            m.weight.data.copy_(
                torch.FloatTensor(w["kernel:0"].value).permute(3, 2, 0, 1)
            )
            m.bias.data.copy_(torch.FloatTensor(w["bias:0"].value))
            numel += m.weight.data.numel()
            numel += m.bias.data.numel()
            k += 1
    try:
        w = f["model_weights"]["conv2d_%d" % k]["conv2d_%d" % k]["kernel:0"]
        print("test failed: ", w.value)
    except:
        print("success, number of parameters copied: %d" % numel)
