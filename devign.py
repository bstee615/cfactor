#!/usr/bin/env python
# coding: utf-8


import shutil
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
parser.add_argument('--slice', default=None)
parser.add_argument('--test', default=None, type=int)
parser.add_argument('--shard-len', default=5000, type=int)
parser.add_argument('--remainder', action='store_true')
parser.add_argument('--no-save', action='store_true')
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
app_log = Path('app.log')
if app_log.exists():
    app_log.unlink()


def do_one(t):
    idx, fn = t
    # print(fn["file_name"])
    code = fn["code"]
    tmp_file_dir = tmp_dir / ('tmp_' + fn["file_name"])
    tmp_file = tmp_file_dir / fn["file_name"]
    tmp_file.parent.mkdir()
    with open(tmp_file, 'w') as f:
        f.write(code)
    try:
        project = factory.make_project(tmp_file)
        new_file, applied = project.apply_all(return_applied=True)
        with open(new_file) as f:
            new_fn = f.read()
        if tmp_file_dir.exists():
            shutil.rmtree(tmp_file_dir)
        parsed = tmp_dir / ('parsed_' + fn["file_name"])
        if parsed.exists():
            shutil.rmtree(parsed)
        return (idx, new_fn, applied)
        #with factory.make_project(tmp_file) as project:
        #    new_file, applied = project.apply_all(return_applied=True)
        #    with open(new_file) as f:
        #        new_fn = f.read()
        #        return (idx, new_fn, applied)
    except:
        tmp_file.unlink()
        raise


def filter_functions(df):
    already_done_indices = set()
    shard_idx = 0
    shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
    while shard_filename.exists():
        with open(shard_filename, 'rb') as f:
            shard = pickle.load(f)
            # print(shard[0])
            for r in shard:
                already_done_indices.add(r[0])
        shard_idx += 1
        shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
    df = df.drop(index=already_done_indices)
    return df


if __name__ == '__main__':
    df = pd.read_json('../4OH4/ReVeal/out/data/chrome_debian_cfg_full_text_files.json')

    if args.mode == 'gen':
        print(len(df), 'samples')

        if args.remainder:
            df = filter_functions(df)
            print('filtered to remainder of', len(df), 'samples')

        if args.test is not None:
            df = df.head(args.test)
            print('cutting to', len(df), 'samples')

        first_row = df.iloc[0]
        func_lines = first_row["code"].splitlines()
        print('Example:')
        print('\n'.join(func_lines[:3]))
        print('...')
        print('\n'.join(func_lines[-3:]))

        func_it = df.iterrows()
        if args.slice is not None:
            begin, end = args.slice.split(':')
            begin, end = int(begin), int(end)
            func_it = itertools.islice(func_it, begin, end)

        factory = refactorings.TransformationsFactory(refactorings.all_refactorings, refactorings.random_picker)
        with tempfile.TemporaryDirectory() as tmp_dir:
            shard_len = args.shard_len

            tmp_dir = Path(tmp_dir)
            print('Working directory:', tmp_dir)
            print('nproc:', nproc)

            def save_shard(new_functions):
                if len(new_functions) > 0 and not args.no_save:
                    shard_idx = 0
                    shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
                    while shard_filename.exists():
                        shard_idx += 1
                        shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
                    print('Saving shard', shard_filename, 'size', len(new_functions))
                    with open(shard_filename, 'wb') as f:
                        pickle.dump(new_functions, f)
            
            new_functions = []
            with multiprocessing.Pool(nproc) as p:
                with tqdm.tqdm(total=len(df)) as pbar:
                    # For very long iterables using a large value for chunksize can make the job complete
                    # much faster than using the default value of 1.
                    for new_func in p.imap_unordered(do_one, func_it, 10):
                        new_functions.append(new_func)
                        pbar.update(1)
                        if len(new_functions) >= shard_len:
                            save_shard(new_functions)
                            new_functions = []
                    save_shard(new_functions)
                        
                #    pbar.update(1)
                #it = tqdm.tqdm(p.imap(do_one, func_it), total=len(functions))
                #while True:
                #    new_functions = list(itertools.islice(it, shard_len))
                #    if len(new_functions) == 0:
                #        break
                #    else:
    elif args.mode == 'diag':

        new_functions = []
        
        shard_idx = 0
        shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
        while shard_filename.exists():
            with open(shard_filename, 'rb') as f:
                new_functions.extend(pickle.load(f))
            shard_idx += 1
            shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
        print(len(new_functions), 'functions total')
        
        total_changed = 0
        showed = 0
        for i, new_code, applied in new_functions:
            old_lines = functions[i]["code"].splitlines(keepends=True)
            new_lines = new_code.splitlines(keepends=True)
            diff = difflib.ndiff(old_lines, new_lines)
            num_changed = sum(1 for l in diff if l[:2] in ('- ', '+ '))
            total_changed += num_changed
            if showed >= 5:
                continue
            print('Applied:', [x.__name__ for x in applied])
            print(''.join(difflib.unified_diff(old_lines, new_lines)))
            showed += 1
        print('Average changed lines:', total_changed / len(new_functions))
