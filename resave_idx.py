"""
Check that the indexes saved in old shard files (indexed by enumerate()) are consistent with dataframe index.
"""
import pandas as pd
from pathlib import Path
import pickle

df = pd.read_json('../4OH4/ReVeal/out/data/chrome_debian_cfg_full_text_files.json')
idx, functions = zip(*list(df.iterrows()))
print('idx is the dataframe index', df.head().index.values, idx[:len(df.head())])

# example indices used to be defined by the indices in enumerate(func_it),
# which may not match the dataframe index.
# We're lucky that we load a dataframe from json, which creates an autoincrementing index starting from 0.
func_it = enumerate(functions)
for i, f in func_it:
    assert f["file_name"] == df.iloc[idx[i]]["file_name"]

shard_idx = 0
shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
while shard_filename.exists():
    with open(shard_filename, 'rb') as f:
        shard = pickle.load(f)
        for r in shard:
            i = r[0]
            assert i in df.index
            assert functions[i]["file_name"] == df.iloc[i]["file_name"]
    shard_idx += 1
    shard_filename = Path(f'new_functions.pkl.shard{shard_idx}')
