
"""Permute Statement: swap 2 independent statements in a basic block."""

from pathlib import Path
import networkx as nx

import cpg


def get_basic_blocks(g):
    """Return a list of all basic blocks, where a block is a list of statements"""
    blocks = []

    cfg = g.edge_subgraph([e for e, d in g.edges.items()
                          if d["type"] == 'FLOWS_TO']).copy()
    node_type = nx.get_node_attributes(g, 'type')
    node_code = nx.get_node_attributes(g, 'code')

    leaders = set()
    for u in cfg.nodes:
        pred = list(cfg.predecessors(u))
        succ = list(cfg.successors(u))
        if len(pred) == 0 or len(pred) > 1:
            leaders.add(u)
        if len(succ) > 1:
            for v in succ:
                leaders.add(v)
        # If none are true, len(pred) == 1 and len(succ) == 1 or 0
    # print('leaders:', leaders)

    def append_if_valid(b, n):
        if node_type[n] in ('ExpressionStatement', 'IdentifierDeclStatement') and len(node_code[n]) > 0:
            b.append(n)
    
    blocks = []
    for l in leaders:
        b = []
        append_if_valid(b, l)
        u = l
        # Add any nodes dominated by l to this basic block
        succ = list(cfg.successors(u))
        while len(succ) == 1:
            u = succ[0]
            succ = list(cfg.successors(u))
            pred = list(cfg.predecessors(u))
            if len(pred) > 1:
                break
            append_if_valid(b, u)
        if len(b) > 0:
            blocks.append(b)

    return blocks


def independent_stmts(basic_block, g):
    """Return a list of pairs of independent statements in a given basic block"""
    independent = []

    ddg = g.edge_subgraph([e for e, d in g.edges.items()
                          if d["type"] in ('REACHES')]).copy()
    ast = g.edge_subgraph([e for e, d in g.edges.items()
                          if d["type"] in ('IS_AST_PARENT')]).copy()
    path_lengths = dict(nx.all_pairs_shortest_path_length(ddg))
    node_type = nx.get_node_attributes(g, 'type')
    node_code = nx.get_node_attributes(g, 'code')

    def depends(u, v):
        """Return true iff u depends on v."""
        data_dependency = False
        if v in path_lengths:
            if u in path_lengths[v]:
                data_dependency = path_lengths[v][u] > 0
        u_id = {node_code[n] for n in nx.descendants(
            ast, u) if node_type[n] == 'Identifier'}
        v_id = {node_code[n] for n in nx.descendants(
            ast, v) if node_type[n] == 'Identifier'}
        shared = u_id.intersection(v_id)
        variable_decl = len(shared) > 0
        return data_dependency or variable_decl

    # a --> i, b --> j, c --> k
    for i in range(len(basic_block)):
        a = basic_block[i]
        for j in range(i+1, len(basic_block)):
            b = basic_block[j]

            if depends(a, b):
                continue
            if depends(b, a):
                continue

            # check statements in between
            skip = False
            for k in range(i+1, j):
                c = basic_block[k]
                if depends(c, a):
                    skip = True
                    break
                if depends(b, c):
                    skip = True
                    break
            if not skip:
                independent.append((a, b))

    return independent


def swap_lines(a, b, g, c_file):
    """Swap 2 lines in a file's text and return the lines in the text"""
    node_location = nx.get_node_attributes(g, 'location')

    def to_line(loc):
        return int(loc.split(':')[0])
    with open(c_file) as f:
        lines = f.readlines()
    a_idx = to_line(node_location[a])-1
    b_idx = to_line(node_location[b])-1
    lines[a_idx], lines[b_idx] = lines[b_idx], lines[a_idx]
    return lines


def permute_stmt(c_file, picker=lambda i: i[0], info=None):
    assert info is not None
    g = cpg.parse(Path(info["project"]), Path(c_file), info["exclude"])
    basic_blocks = get_basic_blocks(g)
    # print('blocks:', basic_blocks)
    candidate_blocks = [b for b in basic_blocks if len(b) > 1]
    # print('candidates:', candidate_blocks)

    independent_pairs = []
    for block in candidate_blocks:
        independent_pairs += independent_stmts(block, g)
    # print('independent pairs:', independent_pairs)
    if len(independent_pairs) == 0:
        return None
    picked = picker(independent_pairs)
    a, b = picked
    new_lines = swap_lines(a, b, g, c_file)

    return new_lines
