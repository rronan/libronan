#!/usr/bin/env python3

from argparse import ArgumentParser
from path import Path


def main():
    args = parse_args()
    print(args)


def parse_args(argv=None):
    parser = ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("."))
    parser.add_argument("-v", action="store_true")
    args = parser.parse_args(argv)
    return args


if __name__ == "__main__":
    main()
