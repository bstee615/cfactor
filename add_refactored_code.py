"""
Load shard data for testing.
"""

from pathlib import Path
import pickle
import pandas as pd
import argparse
import tqdm
import tempfile
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--base')
parser.add_argument('--force', action='store_true')
args = parser.parse_args()

args.base = Path(args.base)
args.raw_code = args.base / 'raw_code'
args.parsed = args.base / 'parsed'
assert args.raw_code.exists()
assert args.parsed.exists()

# Load old code
df = pd.read_json('../4OH4/ReVeal/out/data/chrome_debian_cfg_full_text_files.json')
functions = list(df.iterrows())

# Load new code shards
indexes = []
new_codes = []
shard_idx = 0
shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
while shard_filename.exists():
    with open(shard_filename, 'rb') as f:
        shard = pickle.load(f)
        for idx, new_code, transforms in shard:
            indexes.append(idx)
            new_codes.append(new_code)
    shard_idx += 1
    shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')

old_filenames = df["file_name"].iloc[indexes].values.tolist()
new_filenames = [fname.split('.')[0] + '_refactored.c' for fname in old_filenames]
print(list(zip(old_filenames, new_filenames))[:5])

with tempfile.TemporaryDirectory(prefix=str(Path.cwd().absolute())) as tmpdir:
    for old_filename, new_filename, new_code in tqdm.tqdm(list(zip(old_filenames, new_filenames, new_codes))):
        # Write code file
        old_filepath = args.raw_code / old_filename
        assert old_filepath.exists()

        new_filepath = args.raw_code / new_filename
        if args.force or not new_filepath.exists():
            with open(new_filepath, 'w') as f:
                f.write(new_code)

        # Parse
        old_parsed_dir = args.parsed / old_filename
        assert old_parsed_dir.exists()

        tmpdir = Path(tmpdir)
        assert len(list(tmpdir.glob('*'))) == 0
        parsed = Path('parsed')
        dst_filename = tmpdir / new_filename
        try:
            shutil.copy(new_filepath, dst_filename)
            subprocess.run(f'bash old-joern/joern-parse {tmpdir.absolute()} -outdir {parsed}', shell=True, capture_output=True)
            parsed_file = parsed / str(tmpdir.absolute())[1:]
            assert parsed_file.is_dir()
            new_parsed_dir = args.parsed / new_filename
            if args.force or not new_parsed_dir.exists():
                if new_parsed_dir.exists():
                    shutil.rmtree(new_parsed_dir)
                shutil.copytree(parsed_file, new_parsed_dir)
        finally:
            if dst_filename.exists():
                dst_filename.unlink()
            if parsed.exists():
                shutil.rmtree(parsed)
