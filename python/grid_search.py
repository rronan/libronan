import itertools
import argparse
import yaml
import json
import time
import subprocess
import re
import os
from path import Path


def run(args):
    timestamp = time.strftime("%y%m%d_%H%M%S")
    out = {}
    with open(args.sweep_path, "r") as f:
        opt = yaml.load(f)
    out["fixed"] = opt["fixed"]
    out["sweep"] = opt["sweep"]
    i = 0
    for sweep in opt["sweep"]:
        for values in itertools.product(*sweep.values()):
            cmd = ""
            for k, v in opt["fixed"].items():
                cmd += f"{k} {v} "
            for k, v in zip(sweep.keys(), values):
                cmd += f"{k} {v} "
            cmd = re.sub(r"--[^ ]* _clr_", "", cmd)
            cmd = re.sub(r" +", " ", cmd)
            cmd = re.sub(r"\\", "", cmd)
            name = "_".join([timestamp, args.sweep_name, str(i)])
            cmd += "--name " + name
            if args.preview:
                print(cmd + " --verbose")
            else:
                exclude_nodes = "&".join(["!" + x for x in args.exclude_nodes])
                if len(exclude_nodes) > 0:
                    exclude_nodes = "#$ -l h=" + exclude_nodes
                sh = "\n".join(
                    [
                        "#!/bin/bash",
                        args.shell_intro,
                        exclude_nodes,
                        "export PYTHONPATH=$PYTHONPATH':/sequoia/data1/rriochet'",
                        "export MKL_NUM_THREADS=1",
                        "export NUMEXPR_NUM_THREADS=1",
                        "export OMP_NUM_THREADS=1",
                        'export TORCH_MODEL_ZOO="/sequoia/data1/rriochet/.torch/models"',
                        cmd,
                    ]
                )
                print(sh)
                sh_path = args.outdir / f"_{name}.sh"
                with open(sh_path, "w") as f:
                    f.write(sh)
                try:
                    qsub = " ".join(
                        [
                            "qsub",
                            f"-q {args.q[min(i, len(args.q) - 1)]}",
                            f"-pe serial {args.gpus}",
                            f"-l mem_req={args.mem_req}G,h_vmem={args.h_vmem}G",
                            f'-o "{args.outdir}"',
                            f'-e "{args.outdir}"',
                            f'"{sh_path}"',
                        ]
                    )
                    stdout = subprocess.check_output(qsub, shell=True).decode("utf-8")
                    print(stdout)
                    jobid = re.search("[0-9]+", stdout).group(0)
                finally:
                    if args.cleanup:
                        os.remove(sh_path)
                out[name] = [jobid, args.q[min(i, len(args.q) - 1)], cmd]
                with open(
                    args.outdir / f"{timestamp}_{args.sweep_name}.json", "w"
                ) as f:
                    json.dump(out, f, sort_keys=True, indent=4)
            i += 1
    print(f"cat {args.outdir}/_{timestamp}_{args.sweep_name}_*.o*")
    print(f"cat {args.outdir}/_{timestamp}_{args.sweep_name}_*.e*")
    print(
        f"python /sequoia/data1/rriochet/visualization/html_results.py --indir {args.outdir.parent} --sweep_path {args.outdir}/{timestamp}_{args.sweep_name}.json"
    )
    if not args.preview:
        with open("/sequoia/data1/rriochet/update_html_results.sh", "a") as f:
            f.write(
                f"\npython /sequoia/data1/rriochet/visualization/html_results.py --indir {args.outdir.parent} --sweep_path {args.outdir}/{timestamp}_{args.sweep_name}.json\n"
            )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=".")
    parser.add_argument("--sweep_path", default="sweep.yaml")
    parser.add_argument("--sweep_name", default="sweep")
    parser.add_argument(
        "--shell_intro", default="export PYTHONPATH=/sequoia/data1/rriochet"
    )
    parser.add_argument("--exclude_nodes", nargs="+", default=[])
    parser.add_argument("--q", action="append", type=lambda kv: kv.split("="), dest="q")
    parser.add_argument("--mem_req", type=int, default=20)
    parser.add_argument("--h_vmem", type=int, default=200000)
    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    l = []
    for queue, n in args.q:
        for i in range(int(n)):
            l.append(queue)
    args.q = l
    return args


if __name__ == "__main__":
    args = parse_args()
    print(args)
    run(args)
