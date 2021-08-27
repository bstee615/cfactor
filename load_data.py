"""
Load shard data for testing.
"""

from pathlib import Path
import pickle

shard_idx = 0
shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
while shard_filename.exists():
    with open(shard_filename, 'rb') as f:
        shard = pickle.load(f)
        print(f'{shard_filename}: {len(shard)} samples')
    shard_idx += 1
    shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
