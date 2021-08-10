#!/usr/bin/env python
# coding: utf-8



import refactorings
from pathlib import Path
import difflib
import random
import pandas as pd
import random
import tqdm as tqdm
import tempfile
from contextlib import redirect_stdout
import pickle
import argparse
import subprocess
import multiprocessing
import itertools


parser = argparse.ArgumentParser()
parser.add_argument('--nproc', default='detect')
parser.add_argument('--mode', default='diag')
args = parser.parse_args()

proc = subprocess.run('nproc', capture_output=True)
max_nproc = int(proc.stdout)
if args.nproc == 'detect':
    nproc = max_nproc-1
else:
    nproc = int(args.nproc)
    assert nproc <= max_nproc

errors_log = Path('errors.log')
if errors_log.exists():
    errors_log.unlink()


def do_one(t):
    idx, fn = t
    random.seed(0)
    # print(fn["file_name"])
    code = fn["code"]
    tmp_file = tmp_dir / f'{fn["file_name"]}.c'
    try:
        with open(tmp_file, 'w') as f:
            f.write(code)
        with factory.make_project(tmp_file) as project:
            new_file, applied = project.apply_all(return_applied=True)
            with open(new_file) as f:
                new_fn = f.read()
                return (idx, new_fn, applied)
    except:
        tmp_file.unlink()
        raise


if __name__ == '__main__':
    df = pd.read_json('../4OH4/ReVeal/data/out/data/chrome_debian_cfg_full_text_files.json')
    _, functions = zip(*list(df.iterrows()))

    if args.mode == 'gen':
        print(len(functions), 'samples')

        functions = functions[:24]
        print('cutting to', len(functions), 'samples')

        func_lines = functions[0]["code"].splitlines()
        print('Example:')
        print('\n'.join(func_lines[:3]))
        print('...')
        print('\n'.join(func_lines[-3:]))

        factory = refactorings.TransformationsFactory(refactorings.all_refactorings, refactorings.random_picker)
        with tempfile.TemporaryDirectory() as tmp_dir:
            shards = 0
            shard_len = 5000

            tmp_dir = Path(tmp_dir)
            print('Working directory:', tmp_dir)
            print('nproc:', nproc)
            
            log_filename = 'log.txt'
            print('Redirecting to', log_filename)
            with open(log_filename, 'w') as f:
                with redirect_stdout(f):
                    with multiprocessing.Pool(nproc) as p:
                        it = tqdm.tqdm(p.imap(do_one, enumerate(functions)), total=len(functions))
                        while True:
                            new_functions = list(itertools.islice(it, shard_len))
                            if len(new_functions) == 0:
                                break
                            else:
                                shard_filename = f'new_functions.pkl.shard{shards}'
                                print('Saving shard', shard_filename, 'size', len(new_functions))
                                with open(shard_filename, 'wb') as f:
                                    pickle.dump(new_functions, f)
                                shards += 1
                                del new_functions
    elif args.mode == 'diag':

        with open('new_functions.pkl.shard0', 'rb') as f:
            new_functions = pickle.load(f)
        
        for i, new_code, applied in new_functions:
            print('Applied:', [x.__name__ for x in applied])
            print(''.join(difflib.unified_diff(functions[i]["code"].splitlines(keepends=True), new_code.splitlines(keepends=True))))
