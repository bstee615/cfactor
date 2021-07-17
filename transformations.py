from lxml import etree as et
from pathlib import Path
import copy
import difflib
import networkx as nx

import importlib
import cpg
importlib.reload(cpg)
import srcml
from srcml import xp, E
importlib.reload(srcml)

# ## Refactorings
# Semantics preserving transformations modeled after [tnpa-generalizability](https://github.com/mdrafiqulrabin/tnpa-generalizability).
# Included:
# - Variable Renaming (VN) - renames the name of a variable.
# - Permute Statement (PS) - swaps two independent statements in a basic block.
# - Unused Statement (UN) - inserts an unused string declaration.
# - Loop Exchange (LX) - replaces for loops with while loops or vice versa.
# - Switch to If (SF) - replaces a switch statement with an equivalent if statement.
# Excluded:
# - Boolean Exchange (BX) - switches the value of a boolean variable and propagates this change in the method.

# ### Permute Statement

def count_diff(old_lines, new_lines):
    plus = 0
    minus = 0
    diff_lines = difflib.ndiff(old_lines, new_lines)
    for l in diff_lines:
        if l.startswith('+'):
            plus += 1
        if l.startswith('-'):
            minus += 1
    return plus, minus

# refactoring: Permute Statement

def get_basic_blocks(g):
    blocks = []

    ast = g.edge_subgraph([e for e, d in g.edges.items() if d["type"] == 'IS_AST_PARENT']).copy()
    is_cfg_node = nx.get_node_attributes(ast, 'isCFGNode')
    node_type = nx.get_node_attributes(ast, 'type')

    roots = list(i for i, d in ast.nodes().items() if d["type"] == 'FunctionDef')

    blocks = []
    for r in roots:
        b = []
        q = [r]
        visited = {r}
        while len(q) > 0:
            u = q.pop(0)
            # print(u, node_type[u])
            if is_cfg_node[u]:
                # break_types = ('CompoundStatement', 'IfStatement', 'ElseStatement', 'WhileStatement', 'ForStatement', 'SwitchStatement', 'BreakStatement')
                # if node_type[u].endswith('Statement') and node_type[u] not in break_types:
                if node_type[u] in ('IdentifierDeclStatement', 'ExpressionStatement'):
                    # print('AddToBlock')
                    b.append(u)
                else:
                    # print('NewBlock')
                    if len(b) > 0:
                        blocks.append(b)
                        b = []
            for v in ast.successors(u):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        if len(b) > 0:
            blocks.append(b)
            b = []

    return blocks

def independent_stmts(basic_block, g):
    independent = []

    # old-joern
    pdg = g.edge_subgraph([e for e, d in g.edges.items() if d["type"] in ('CONTROLS', 'REACHES')]).copy()
    ast = g.edge_subgraph([e for e, d in g.edges.items() if d["type"] in ('IS_AST_PARENT')]).copy()
    path_lengths = dict(nx.all_pairs_shortest_path_length(pdg))
    node_type = nx.get_node_attributes(g, 'type')
    node_code = nx.get_node_attributes(g, 'code')

    def depends(u, v):
        """Return true iff u depends on v."""
        data_dependency = False
        if v in path_lengths:
            if u in path_lengths[v]:
                data_dependency = path_lengths[v][u] > 0
        u_id = {node_code[n] for n in nx.descendants(ast, u) if node_type[n] == 'Identifier'}
        v_id = {node_code[n] for n in nx.descendants(ast, v) if node_type[n] == 'Identifier'}
        shared = u_id.intersection(v_id)
        variable_decl = len(shared) > 0
        # print(data_dependency, variable_decl, u, v, u_id, v_id, shared)
        return data_dependency or variable_decl

    # a --> i, b --> j, c --> k
    for i in range(len(basic_block)):
        a = basic_block[i]
        for j in range(i+1,len(basic_block)):
            b = basic_block[j]

            # Check two statements
            if depends(a, b):
                # print('a depends b', a, 'depends', b)
                continue
            if depends(b, a):
                # print('b depends a', b, 'depends', a)
                continue

            # check statements in between
            skip = False
            for k in range(i+1, j):
                c = basic_block[k]
                # a is moving to the end but an in-between statement depends on it
                if depends(c, a):
                    # print('c depends a', c, 'depends', a)
                    skip = True
                    break
                # c is moving to the beginning but the ending statement depends on it
                if depends(b, c):
                    # print('b depends c', b, 'depends', c)
                    skip = True
                    break
            if not skip:
                independent.append((a, b))

    return independent

def swap_lines(a, b, g, c_file):
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
    g = cpg.parse(Path(info["project"]), Path(c_file))
    basic_blocks = get_basic_blocks(g)
    # print('starting basic blocks:', basic_blocks)
    candidate_blocks = [b for b in basic_blocks if len(b) > 1]
    # print('candidate basic blocks:', candidate_blocks)

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

def test_permute_stmt():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = permute_stmt(c_file, info={"project": 'tests/testbed'})
    assert count_diff(old_lines, new_lines) == (1, 1)
    
    c_file = Path('tests/abm/594/nonul2.c')
    # Should only be 1 independent pair
    new_lines = permute_stmt(c_file, info={"project": 'tests/abm/594'})


# In[88]:


# Refactoring: rename variable 

def rename_variable(c_file, picker=lambda i: i[0], info=None):
    root = srcml.get_xml_from_file(c_file)
    all_names = xp(root, f'//src:function//src:decl_stmt/src:decl/src:name')
    if len(all_names) == 0:
        return None
    target_name_node = picker(all_names)
    old_target_name = target_name_node.text

    new_target_name = 'fungus'

    function_name = xp(xp(target_name_node, './ancestor::src:function')[0], './src:name')[0].text
    targets = xp(root, f'//src:name[text() = "{old_target_name}"][ancestor::src:function[./src:name[text() = "{function_name}"]]]')
    assert len(targets) > 0, 'No variable reference queried'
    for target in targets:
        target.text = new_target_name
    
    new_code = srcml.get_code(root)
    return new_code.splitlines(keepends=True)

def test_rename_variable():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = rename_variable(c_file, info={"project": 'tests/testbed'})
    assert count_diff(old_lines, new_lines) == (5, 5)


# In[101]:


# Refactoring: insert noop
def insert_noop(c_file, picker=lambda i: i[0], info=None):
    g = cpg.parse(Path(info["project"]), Path(c_file))
    all_targets = [d["location"] for n, d in g.nodes.items() if d["type"] == 'ExpressionStatement' and isinstance(d["location"], str)]
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

def test_insert_noop():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = insert_noop(c_file, info={"project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (1, 0)


# In[108]:


# Refactoring: exchange switch with if/else
from collections import OrderedDict

def get_stmts_by_case(switch):
    """
    Return an ordered mapping of executable statements to their respective case ranges.
    Switch cases have peculiar control flow because of default and fallthrough.
    The only fallthroughs we handle are ones where all cases in the fallthrough have the
    same executable statements. For example, this switch is not handled:
    We only handle defaults if they come after all cases.
    """
    block_content = xp(switch, './src:block/src:block_content')[0]
    stmts_by_case = OrderedDict()
    cases_key = None
    cases = []

    # Parse all executable statements (stmt) from the switch.
    for node in block_content:
        if srcml.tagname(node) == 'case' or srcml.tagname(node) == 'default':
            cases.append(node)
            cases_key = tuple(copy.deepcopy(cases))
        else:
            if cases_key not in stmts_by_case:
                stmts_by_case[cases_key] = []
            stmts_by_case[cases_key].append(node)
            if srcml.tagname(node) in ['break', 'return']:
                cases = []

    # All blocks of executable statements must end with a "break;"
    for cases, stmts in stmts_by_case.items():
        tag_name = srcml.tagname(stmts[-1])
        if tag_name == 'break':
            stmts.pop()
        elif tag_name == 'return':
            pass
        else:
            raise Exception(f'Unknown statement tag ends a switch: {tag_name}')

    # Disallow all fallthrough blocks because they are not sound
    def get_case_text(cases):
        """Get the text inside a collection of cases"""
        result = set()
        for c in cases:
            expr = xp(c, './/src:expr')
            if len(expr) > 0:
                result.add(''.join(expr[0].itertext()))
            else:
                result.add('default')
        return result
    items = list(stmts_by_case.items())
    for i in range(len(items)-1):
        cases = items[i][0]
        assert not get_case_text(cases).issubset(get_case_text(items[i+1][0])), 'Fallthroughs are not supported!'

    return stmts_by_case

def gen_if_stmt(switch):
    """Generate a big if_stmt (if/elif/else) from a switch statement"""

    stmts_by_case = get_stmts_by_case(switch)
    narrow_ws = srcml.get_space(xp(switch, './src:condition')[0], 'back')
    wide_ws = srcml.get_space(xp(switch, './src:block/src:block_content')[0], 'front')
    condition_variable = copy.deepcopy(xp(switch, './src:condition/src:expr')[0])
    condition_variable.tail = '\n'
    IF, ELIF, ELSE = range(3)  # Type of conditional to generate

    def gen_conditional(cases, stmts, if_type):
        """Generate and return a conditional (if/elif/else for a switch case)"""

        if if_type in [IF, ELIF]:
            # Generate a boolean condition expression or'ing together all cases
            sub_exprs = []
            for i, case in enumerate(cases):
                if srcml.tagname(case) == 'case':
                    case_value = xp(case, './src:expr')[0]
                    case_value.tail = '\n'
                    sub_expr = E.expr(copy.deepcopy(condition_variable), ' ', E.operator('=='), case_value)
                    sub_exprs.append(sub_expr)
                if i < len(cases) - 1:
                    sub_exprs.append(E.operator('||'))
            stmts[-1].tail = '\n'
            condition = E.expr(*sub_exprs)

        # We have to use __call__ because calling a funcition named "if" is a syntax error
        if if_type == IF:
            return E.__call__('if', 'if ', E.condition('(', condition, ')'), narrow_ws, E.block('{', E.block_content(wide_ws, *stmts), '}'))
        elif if_type == ELIF:
            return E.__call__('if', 'else if ', E.condition('(', condition, ')'), narrow_ws, E.block('{', E.block_content(wide_ws, *stmts), '}'), type='elseif')
        elif if_type == ELSE:
            return E.__call__('else', 'else ', narrow_ws, E.block('{', E.block_content(wide_ws, *stmts)), narrow_ws, '}')
        else:
            raise

    items = list(stmts_by_case.items())
    ifs = []
    # Move default to last if it is alone
    for i, (cases, stmts) in enumerate(items):
        if any(srcml.tagname(c) == 'default' for c in cases):
            default = items.pop(i)
            items.append(default)
            break
    for i, (cases, stmts) in enumerate(items):
        ifs.append(narrow_ws)
        if any(srcml.tagname(c) == 'default' for c in cases):
            ifs.append(gen_conditional(cases, stmts, ELSE))
        elif i == 0:
            ifs.append(gen_conditional(cases, stmts, IF))
        else:
            ifs.append(gen_conditional(cases, stmts, ELIF))
    if_stmt = E.if_stmt(*ifs, narrow_ws)
    return if_stmt

def switch_exchange(c_file, picker=lambda i: i[0], info=None):
    root = srcml.get_xml_from_file(c_file)
    all_switches = xp(root, f'//src:switch')
    if len(all_switches) == 0:
        return None
    target = picker(all_switches)
    if_stmt = gen_if_stmt(target)
    target.getparent().replace(target, if_stmt)
    return srcml.get_code(root).splitlines(keepends=True)

def test_switch_exchange():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = switch_exchange(c_file)
    assert count_diff(old_lines, new_lines) == (17, 9)


# In[111]:

import dataclasses

@dataclasses.dataclass
class JoernLocation:
    line: int  # 1-indexed
    column_idx: int  # All others 0-indexed
    offset: int
    end_offset: int

    @staticmethod
    def fromstring(location):
        return JoernLocation(*map(int, location.split(':')))


# Refactoring: exchange for loop with while

import re
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

    # CompoundStatements don't have reliable code locations,
    # so get the last statement of the loop body
    stmt_is_compound = node_type[stmt] == 'CompoundStatement'
    if stmt_is_compound:
        stmt = max(g.successors(stmt), key=lambda n: node_childNum[n])
    
    # Get code and location for the interesting nodes
    cond_code = node_code[cond]
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
    new_text += init_code + '\n'
    new_text += loop_indent + f'while ({cond_code})'
    if not stmt_is_compound:
        new_text += ' {'
    new_text += text[loop_loc.end_offset+1:stmt_loc.end_offset+1] + '\n'
    new_text += body_indent + post_code + ';\n'
    new_text += loop_indent + '}\n'
    new_text += text[proceed_from:]
    lines = new_text.splitlines(keepends=True)
    return lines

def test_loop_exchange():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, picker=lambda x: x[0], info={"project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = loop_exchange(c_file, picker=lambda x: x[1], info={"project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = loop_exchange(c_file, picker=lambda x: x[2], info={"project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (4, 1)

    c_file = Path('tests/ctestsuite/069/into2.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, info={"project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (5, 2)

    c_file = Path('tests/abm/575/into3.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, info={"project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (5, 2)


# In[ ]:




