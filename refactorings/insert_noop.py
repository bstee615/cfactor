"""Insert Noop: insert a statement that doesn't affect any other variables."""

from pathlib import Path
import cpg


def insert_noop(c_file, picker=lambda i: i[0], info=None):
    g = cpg.parse(Path(info["project"]), Path(c_file))
    all_targets = [d["location"] for n, d in g.nodes.items(
    ) if d["type"] == 'ExpressionStatement' and isinstance(d["location"], str)]
    if len(all_targets) == 0:
        return None
    location = picker(all_targets)
    target_line = int(location.split(':')[0])
    target_idx = target_line - 1

    new_name = 'mungus'

    import random
    typename, value = random.choice([
        ('int', '123'),
        ('char', '\'a\''),
        ('char *', '"hello"'),
    ])

    with open(c_file) as f:
        lines = f.readlines()
    indent = lines[target_idx][:-len(lines[target_idx].lstrip())]
    lines.insert(target_idx, f'{indent}{typename} {new_name} = {value};\n')
    return lines
