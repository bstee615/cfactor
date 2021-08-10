from collections import defaultdict
import functools
import pandas as pd
from pathlib import Path
import re

def corebench_manual():
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

def synthetic(project):
    flaws = set()
    files = list(project.buggy_path.glob('*/*/*.c') + project.buggy_path.glob('*/*.c') + project.buggy_path.glob('*.c'))
    assert len(files) > 0, project.buggy_path
    for fname in files:
        with open(fname) as f:
            for i, line in enumerate(f.readlines(), start=1):
                if project.program in 'abm':
                    if re.search(r'/\*\s*BAD\s*\*/', line):
                        flaws.add((fname, int(i)))
                elif project.program == 'zitser':
                    if re.search(r'/\*\s*BAD\s*\*/', line):
                        flaws.add((fname, int(i+1)))
                elif project.program == 'ctestsuite':
                    if re.search(r'/\*\s*FLAW\s*\*/', line):
                        flaws.add((fname, int(i)))
                elif project.program == 'toyota':
                    if re.search(r'/\*\s*ERROR', line):
                        flaws.add((fname, int(i)))
    return flaws

def get_all(projects):
    corebench_groundtruth = {}
    corebench_groundtruth.update(corebench_manual())
    corebench_groundtruth.update(dbgbench(projects))
    for proj in projects:
        if proj.program in corebench_groundtruth:
            flaws = corebench_groundtruth[proj.program][proj.buggy]
        else:
            flaws = synthetic(proj)
        # print(proj.program, proj.buggy, len(flaws))
        proj.flaws = flaws
    return projects
