from pydoc import locate
import json

from tqdm import tqdm
from torch.utils.data import DataLoader

from libronan.python.utils import save_args


def make_model(model, args, load, gpu, data_parallel):
    model = locate(model)(args)
    if load is not None:
        model.load(load)
    if gpu:
        model.gpu()
    if data_parallel:
        model.data_parallel()
    print(f"n parameters: {model.get_num_parameters()}")
    return model


def make_loader(dataset, args, set_, bsz, num_workers, pin_memory, shuffle=True):
    dataset = locate(dataset)(args, set_)
    loader = DataLoader(
        dataset,
        bsz,
        num_workers=num_workers,
        shuffle=shuffle,
        drop_last=True,
        pin_memory=pin_memory,
    )
    return loader


def process_batch(model, batch, loss, set_, j):
    res = model.step(batch, set_)
    for key, value in res.items():
        try:
            loss[key] = (loss[key] * j + value) / (j + 1)
        except KeyError:
            loss[key] = value
    return loss


def process_epoch(model, set_, loader, log, i, n, callback=None, verbose=True):
    loss = {}
    pbar = tqdm(loader, dynamic_ncols=True, leave=False)
    for j, batch in enumerate(pbar):
        loss = process_batch(model, batch, loss, set_, j)
        if verbose:
            pbar.set_description(
                f"{set_} {i}/{n - 1}, "
                + " | ".join(f"{k}: {v:.4e}" for k, v in loss.items())
            )
        else:
            pbar.set_description(f"{set_} {i}/{n - 1}")
        for key, value in loss.items():
            log[i][f"{set_}_{key}"] = value
        if callback is not None and (j + 1) % callback[1] == 0:
            callback[0](f"{i:03d}_{j:06d}_", log)
    return log


def train(model, loader_dict, n_epochs, checkpoint_func, subcheck=None, verbose=True):
    callback = (checkpoint_func, subcheck) if subcheck is not None else None
    log = []
    for i in range(n_epochs):
        log.append({"epoch": i})
        for set_, loader in loader_dict.items():
            process_epoch(model, set_, loader, log, i, n_epochs, callback, verbose)
        log[i]["lr"] = model.get_lr()
        checkpoint_func(f"{i:03d}", log)
        print(log[i])
        model.scheduler.step(log[-1]["val_loss"])
        if model.get_lr() < 5e-9:
            break


def checkpoint(epoch, log, model=None, args=None):
    args.checkpoint.mkdir_p()
    if args is not None:
        save_args(args.checkpoint / "args.json", args)
    with open(args.checkpoint / "log.json", "w") as f:
        json.dump(log, f, indent=4)
    if args.save_all:
        model.save(args.checkpoint, epoch)
    if args.save_last:
        model.save(args.checkpoint, "last")
    if "val_loss" in log[-1]:
        if log[-1]["val_loss"] == min([x["val_loss"] for x in log]):
            model.save(args.checkpoint, "best")
