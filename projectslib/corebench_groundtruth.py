from collections import defaultdict
import functools
import pandas as pd
from pathlib import Path

def manual():
    result = defaultdict(functools.partial(defaultdict, list))
    df = pd.read_csv('corebench_manual_groundtruth.tsv', delimiter='\t')
    for _, row in df.iterrows():
        for buggy_line in row["Line of Bug Crash"].split(','):
            buggy_line = int(buggy_line)
            result[row["Project"]][row["Buggy"]].append((row["File of Bug"], buggy_line))
    # Convert to a normal dict
    result = dict(result)
    for k in result:
        result[k] = dict(result[k])
    return result

def dbgbench(projects):
    dbgbench = Path('dbgbench.github.io')
    faultstxts = dbgbench.glob('*.faults.txt')
    result = defaultdict(functools.partial(defaultdict, list))
    for faultstxt in faultstxts:
        project_name, ok = faultstxt.name.split('.')[:2]
        if project_name == 'find':
            project_name = 'findutils'
        project = next((p for p in projects if p.program == project_name and p.ok == ok), None)
        if project is not None:
            with open(faultstxt) as f:
                for l in f.readlines():
                    filename, lineno = l.split(':')
                    lineno = int(lineno)
                    result[project.program][project.buggy].append((filename, lineno))
    # Convert to a normal dict
    result = dict(result)
    for k in result:
        result[k] = dict(result[k])
    return result

def get(projects):
    groundtruth = {}
    groundtruth.update(manual())
    groundtruth.update(dbgbench(projects))
    return groundtruth
