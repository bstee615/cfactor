#!/usr/bin/env python
# coding: utf-8


import argparse
import difflib
import itertools
import multiprocessing
import pickle
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import tqdm as tqdm

import refactorings
from cfactor.refactorings.project import TransformationProject
from data_processing.create_ggnn_input import get_input

import logging
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-i', "--input_dir", help="Input source code files", default='../data/chrome_debian')
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
    nproc = max_nproc - 1
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
    try:
        with TransformationProject(refactorings.all_refactorings, refactorings.random_picker,
                                   fn["file_name"], fn["code"]) as project:
            new_lines, applied = project.apply_all(return_applied=True)
            if new_lines is not None:
                return idx, ''.join(new_lines), applied
            else:
                return idx, new_lines, applied
    except Exception as e:
        logger.exception('idx %d filename %s had an error', idx, fn["file_name"], exc_info=e)
    finally:
        pass


def filter_functions(df):
    already_done_indices = set()
    existing, _ = get_shards()
    for shard in existing:
        with open(shard, 'rb') as f:
            shard = pickle.load(f)
            for r in shard:
                already_done_indices.add(r[0])
    df = df.drop(index=already_done_indices)
    return df


def get_shards():
    existing_shards = []
    shard_idx = 0
    shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
    while shard_filename.exists():
        shard_idx += 1
        shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
    new_shard = shard_filename
    return existing_shards, new_shard


def main():
    json_data = get_input(Path(args.input_dir))
    if args.test is not None:
        json_data = itertools.islice(json_data, args.test)
        logger.info('cutting to %d samples', args.test)
    df = pd.DataFrame(data=json_data)
    if args.mode == 'gen':
        logger.info('%d samples', len(df))

        if args.remainder:
            df = filter_functions(df)
            logger.info('filtered to remainder of %d samples', len(df))

        func_it = df.iterrows()
        if args.slice is not None:
            begin, end = args.slice.split(':')
            begin, end = int(begin), int(end)
            func_it = itertools.islice(func_it, begin, end)

        shard_len = args.shard_len

        logger.info('nproc: %d', nproc)

        def save_shard(data):
            if len(data) > 0 and not args.no_save:
                _, new_shard = get_shards()
                with open(new_shard, 'wb') as f:
                    pickle.dump(data, f)

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
    elif args.mode == 'diag':

        new_functions = []

        logger.info('%d functions total', len(new_functions))

        functions_idx, functions = zip(*list(df.iterrows()))

        total_changed = 0
        showed = 0
        for i, new_code, applied in new_functions:
            old_lines = functions[i]["code"].splitlines(keepends=True)
            new_lines = new_code.splitlines(keepends=True)
            diff = difflib.ndiff(old_lines, new_lines)
            num_changed = sum(1 for line in diff if line[:2] in ('- ', '+ '))
            total_changed += num_changed
            if showed >= 5:
                continue
            logger.info('Applied: %s', [x.__name__ for x in applied])
            logger.info(''.join(difflib.unified_diff(old_lines, new_lines)))
            showed += 1
        
        logger.info('Average changed lines: %s', total_changed / len(new_functions if new_functions != 0 else 1))


if __name__ == '__main__':
    main()
