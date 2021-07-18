"""Loop exchange: exchange for loop with while"""

import dataclasses
from pathlib import Path
import networkx as nx
import cpg

@dataclasses.dataclass
class JoernLocation:
    line: int  # 1-indexed
    column_idx: int  # All others 0-indexed
    offset: int
    end_offset: int

    @staticmethod
    def fromstring(location):
        return JoernLocation(*map(int, location.split(':')))


def loop_exchange(c_file, picker=lambda i: i[0], info=None):
    g = cpg.parse(Path(info["project"]), Path(c_file))
    ast = g.edge_subgraph([e for e, d in g.edges.items() if d["type"] == 'IS_AST_PARENT']).copy()
    with open(c_file) as f:
        text = f.read()
    lines = text.splitlines(keepends=True)

    node_type = nx.get_node_attributes(ast, 'type')
    node_code = nx.get_node_attributes(ast, 'code')
    node_loc = nx.get_node_attributes(ast, 'location')
    node_childNum = nx.get_node_attributes(ast, 'childNum')

    # Pick a loop
    all_loops = [n for n, d in ast.nodes.items() if d["type"] == 'ForStatement']
    if len(all_loops) == 0:
        return None
    loop = picker(all_loops)

    # Get child nodes
    succ = ast.successors(loop)
    init, cond, post, stmt = succ

    def get_last_stmt(node):
        return max(g.successors(node), key=lambda n: node_childNum[n])

    # CompoundStatements don't have reliable code locations,
    # so get the last statement of the loop body
    stmt_is_compound = node_type[stmt] == 'CompoundStatement'
    if stmt_is_compound:
        first_stmt_line = JoernLocation.fromstring(node_loc[get_last_stmt(stmt)]).line
    else:
        first_stmt_line = JoernLocation.fromstring(node_loc[stmt]).line
    # These statements have locations that have unusable end_offsets
    janky_location_stmts = (
        'CompoundStatement',
        'IfStatement', 'ElseStatement',
        'ForStatement', 'WhileStatement',
        'SwitchStatement',
    )
    # Find a node with a location with an end_offset we can use
    while node_type[stmt] in janky_location_stmts:
        stmt = get_last_stmt(stmt)
    # Correct the ending offset
    stmt_loc = JoernLocation.fromstring(node_loc[stmt])
    assert stmt_loc.offset != stmt_loc.end_offset  # Sanity check!
    if node_type[list(ast.predecessors(stmt))[0]] == 'CompoundStatement':
        stmt_end_offset = text.find('}\n', stmt_loc.end_offset)
    else:
        stmt_end_offset = stmt_loc.end_offset
    # The other fields of this variable are not very reliable.
    # Make sure we don't introduce a bug by using it.
    del stmt_loc
    
    # Get code and location for the interesting nodes
    cond_code = node_code[cond]
    init_code = node_code[init]
    post_code = node_code[post]
    loop_loc = JoernLocation.fromstring(node_loc[loop])
    
    # Get the correct whitespace to indent the loop and the body
    loop_indent = lines[loop_loc.line-1][:-len(lines[loop_loc.line-1].lstrip())]
    body_indent = lines[first_stmt_line-1][:-len(lines[first_stmt_line-1].lstrip())]

    # Get the last character of the for loop's body
    if stmt_is_compound:
        seek = '}\n'
    else:
        seek = '\n'
    proceed_from = text.find(seek, stmt_end_offset + 1) + len(seek)

    # Replace for loop with while inplace (preserves most whitespace automatically)
    new_text = text[:loop_loc.offset]
    new_text += init_code + '\n'
    new_text += loop_indent + f'while ({cond_code})'
    if not stmt_is_compound:
        new_text += ' {'
    new_text += text[loop_loc.end_offset+1:stmt_end_offset + 1] + '\n'
    new_text += body_indent + post_code + ';\n'
    new_text += loop_indent + '}\n'
    new_text += text[proceed_from:]
    lines = new_text.splitlines(keepends=True)
    return lines
