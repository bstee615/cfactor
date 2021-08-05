"""Insert Noop: insert a statement that doesn't affect any other variables."""

from pathlib import Path
import networkx as nx
import cpg


def insert_noop(c_file, picker=lambda i: i[0], info=None):
    g = cpg.parse(Path(info["project"]), Path(c_file), info["exclude"])
    ast = g.edge_subgraph([e for e, d in g.edges.items() if d["type"] == 'IS_AST_PARENT']).copy()
    node_type = nx.get_node_attributes(g, 'type')
    node_location = nx.get_node_attributes(g, 'location')
    def is_target(n):
        is_valid_stmt = node_type[n] in ('ExpressionStatement', 'IfStatement', 'ElseStatement', 'ForStatement', 'WhileStatement')
        has_valid_location = isinstance(node_location[n], str)
        pred = list(ast.predecessors(n))
        if len(pred) > 0:
            parent_is_compound = node_type[pred[0]] == 'CompoundStatement'
        else:
            parent_is_compound = False
        return is_valid_stmt and parent_is_compound and has_valid_location
    all_targets = [node_location[n] for n in filter(is_target, ast.nodes)]
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
