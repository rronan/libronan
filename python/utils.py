from io import BytesIO
from zipfile import ZipFile
from copy import copy
import random
from collections import defaultdict
import json
import hashlib

import argparse
#import torch
import numpy as np
import requests
from PIL import Image


def set_seed(seed, gpu):
    random.seed(seed)
    torch.manual_seed(seed)
    if gpu:
        torch.cuda.manual_seed_all(seed)


def parse_slice(s):
    a_list = []
    for a in s.split(':'):
        try:
            a_list.append(int(a))
        except ValueError:
            a_list.append(None)
    while len(a_list) < 3:
        a_list.append(None)
    return slice(*a_list)


def write_slice(s):
    return f"{s.start if s.start is not None else ''}:{s.stop if s.start is not None else ''}"


def write_namespace(s):
    out = []
    for k,v in vars(s).items():
        if type(v) is not bool or v:
            out.append('--' + k)
            if type(v) is bool:
                out.append('\"\"')
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


def save_args(path, args, zf=None):
    args_copy = copy(args)
    for k,v in vars(args_copy).items():
        if type(v) is slice:
            vars(args_copy)[k] = write_slice(v)
        elif type(v) is argparse.Namespace:
            vars(args_copy)[k] = write_namespace(v)
    if zf is None:
        with open(path, 'w') as f:
            json.dump(vars(args_copy), f, indent=4, sort_keys=True)
    else:
        zf.writestr(
            str(path).replace('/', '\\'),
            json.dumps(vars(args_copy), indent=4, sort_keys=True)
        )

def image2mask(arr, color_list):
    res = np.zeros(arr.shape[:2])
    for i,c in enumerate(color_list):
        mask = (arr == np.array(c)[:3]).all(axis=2)
        res += (i + 1) * mask
    return res


def binmask2image(arr, color_list):
    im = np.zeros((arr.shape[1], arr.shape[2], 3))
    for m,c in zip(arr, [[0,0,0]] + color_list):
        im += np.repeat(np.expand_dims(m,axis=-1),3,axis=-1) * np.array(c)
    return im.astype('uint8')


def mask2image(arr, color_list):
    im = np.zeros((*arr.shape, 3))
    for i,c in enumerate(color_list):
        im += (np.repeat(np.expand_dims(arr==(i+1), axis=-1), 3, axis=-1)
               * np.array(c))
    return im.astype('uint8')


def array2image(array, normalize=False):
    u = np.unique(array)
    q1, q3 = np.percentile(u, 25), np.percentile(u, 75)
    array = (array - (q1 + q3) / 2) / (q3 - q1) / 1.7 # 1.7 scales contrast
    array = (array * 255 + 127).clip(0, 255)
    image = Image.fromarray(array.astype('uint8')).convert('RGB')
    return image


def tensor2image(tensor, normalize=False):
    array = tensor.clone().detach().cpu().numpy()
    image = array2image(array, normalize)
    return image


def ptpb(im):
    byteimage = BytesIO()
    try:
        im.save(byteimage, format='PNG', compress=1)
    except AttributeError:
        im.savefig(byteimage)
    files = {'c': ('foo.png', byteimage.getvalue())}
    response = requests.post('https://ptpb.pw/', files=files)
    print(response.content.decode("utf-8"))

def tis(im):
    byteimage = BytesIO()
    try:
        im.save(byteimage, format='PNG', compress=1)
    except AttributeError:
        im.savefig(byteimage)
    image_hash = hashlib.sha256(im.tobytes()).hexdigest()
    name = f"/sequoia/data1/rriochet/image_server/{image_hash}.png"
    im.save(name)
    print(f"http://localhost:8000/{image_hash}.png")



