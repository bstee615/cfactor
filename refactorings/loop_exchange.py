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
    g = cpg.parse(Path(info["project"]), Path(c_file), info["exclude"])
    ast = g.edge_subgraph([e for e, d in g.edges.items() if d["type"] == 'IS_AST_PARENT']).copy()
    # If file has CRLF line endings, then it will screw with Python's counting the file offsets.
    with open(c_file, newline='\r\n') as f:
        text = f.read()
    if '\r' in text:
        raise Exception(f'{c_file} is CRLF')
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
    succ = list(ast.successors(loop))
    if len(succ) == 4:
        init, cond, post, stmt = succ
        assert node_type[init] == 'ForInit', f'expected \'ForInit\' got {node_type[init]}'
    elif len(succ) == 3:
        init = None
        cond, post, stmt = succ
    else:
        raise Exception('Unexpected loop subtree structure')
    assert node_type[cond] == 'Condition'
    assert node_type[stmt].endswith('Statement')

    # Some statements are disqualified
    janky_location_stmts = (
        'CompoundStatement',
        'IfStatement', 'ElseStatement',
        'ForStatement', 'WhileStatement',
        'SwitchStatement',
    )
    # CompoundStatements don't have reliable code locations,
    # so get the last statement of the loop body
    stmt_is_compound = node_type[stmt] == 'CompoundStatement'
    if stmt_is_compound:
        stmt = max(g.successors(stmt), key=lambda n: node_childNum[n])
        if node_type[stmt] in janky_location_stmts:
            raise Exception('Loop does not qualify because its last statement has insufficient location info')
    assert node_type[stmt].endswith('Statement')
    
    # Get code and location for the interesting nodes
    cond_code = node_code[cond]
    if init is not None:
        init_code = node_code[init]
    post_code = node_code[post]
    loop_loc = JoernLocation.fromstring(node_loc[loop])
    stmt_loc = JoernLocation.fromstring(node_loc[stmt])
    
    # Get the correct whitespace to indent the loop and the body
    loop_indent = lines[loop_loc.line-1][:-len(lines[loop_loc.line-1].lstrip())]
    body_indent = lines[stmt_loc.line-1][:-len(lines[stmt_loc.line-1].lstrip())]

    # Get the last character of the for loop's body
    if stmt_is_compound:
        seek = '}\n'
    else:
        seek = '\n'
    proceed_from = text.find(seek, stmt_loc.end_offset + 1) + len(seek)

    # Replace for loop with while inplace (preserves most whitespace automatically)
    new_text = text[:loop_loc.offset]
    if init is not None:
        new_text += init_code + '\n' + loop_indent
    new_text += f'while ({cond_code})'
    if not stmt_is_compound:
        new_text += ' {'
    new_text += text[loop_loc.end_offset+1:stmt_loc.end_offset+1] + '\n'
    new_text += body_indent + post_code + ';\n'
    new_text += loop_indent + '}\n'
    new_text += text[proceed_from:]
    lines = new_text.splitlines(keepends=True)
    return lines
