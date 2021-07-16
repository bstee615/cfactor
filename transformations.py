#!/usr/bin/env python
# coding: utf-8

# # Modifying AST with `srcml`
# Parses very OK! Can we modify??

# In[77]:


# Imports
from lxml import etree as et
from lxml.builder import ElementMaker
import subprocess
from pathlib import Path
import copy
import re
import difflib
import networkx as nx

import cpg
import importlib
importlib.reload(cpg)

srcml_exe = 'srcml/bin/srcml'
namespaces={'src': 'http://www.srcML.org/srcML/src'}
E = ElementMaker(namespace="http://www.srcML.org/srcML/src")


# In[78]:


# Print XML from root
def prettyprint(node):
    print(et.tostring(node, encoding="unicode", pretty_print=True))
# prettyprint(xmldata)

def xp(node, xpath):
    return node.xpath(xpath, namespaces=namespaces)

def start_pos(node):
    # prettyprint(node)
    return node.get('{http://www.srcML.org/srcML/position}start')

def get_space(node, front_back):
    if front_back == 'front':
        regex = rf'^<{et.QName(node).localname}[^>]+>(\s+)'
    elif front_back == 'back':
        regex = r'(\s+)$'
    else:
        raise
    m = re.search(regex, et.tostring(node, encoding='unicode'))
    if m:
        return m.group(1)
    else:
        return ''


# In[83]:


# Functions for running srcml command.
def srcml(filepath):
    """Run srcml.
    If the filepath is a .c file, return xml tree as lxml ElementTree.
    If the filepath is an .xml file, return source code as a string."""
    assert filepath.exists()
    args = [srcml_exe, filepath]
    args = [str(a) for a in args]
    if filepath.suffix == '.c':
        args += ['--position']
    # print('Running SrcML:', ' '.join(args))
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        print('Error', proc.returncode)
        print(proc.stderr)
        return None
    if filepath.suffix == '.xml':
        return proc.stdout.decode('utf-8')
    elif filepath.suffix == '.c':
        # with open(str(filepath) + '.xml', 'wb') as f:
        #     f.write(proc.stdout)
        xml = et.fromstring(proc.stdout)
        return xml

def get_xml(c_code):
    tmp = Path('/tmp/code.c')
    with open(tmp, 'w') as f:
        f.write(c_code)
    return xp(srcml(tmp), '//src:unit')[0]

def get_xml_from_file(c_file):
    return xp(srcml(c_file), '//src:unit')[0]

def get_code(xml_root):
    tmp = Path('/tmp/code.xml')
    with open(tmp, 'w') as f:
        f.write(et.tostring(xml_root, encoding='unicode'))
    return srcml(tmp)

if __name__ == '__main__':
    fname = Path('tests/testbed/testbed.c')
    root = get_xml_from_file(fname)
    get_code(root)
    with open(fname) as f:
        root = get_xml(f.read())
        get_code(root)


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

# #### srcML



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

if __name__ == '__main__':
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = permute_stmt(c_file, info={"project": 'tests/testbed'})
    print(''.join(difflib.unified_diff(old_lines, new_lines)))


# In[88]:


# Refactoring: rename variable 
from random_word import RandomWords
words = RandomWords()

def rename_variable(c_file, picker=lambda i: i[0], info=None):
    root = get_xml_from_file(c_file)
    all_names = xp(root, f'//src:function//src:decl_stmt/src:decl/src:name')
    if len(all_names) == 0:
        return None
    target_name_node = picker(all_names)
    old_target_name = target_name_node.text

    new_target_name = words.get_random_word()
    while '-' in new_target_name:
        new_target_name = words.get_random_word()

    function_name = xp(target_name_node, './ancestor::src:function')[0].xpath('./src:name', namespaces=namespaces)[0].text
    targets = xp(root, f'//src:name[text() = "{old_target_name}"][ancestor::src:function[./src:name[text() = "{function_name}"]]]')
    assert len(targets) > 0
    for target in targets:
        target.text = new_target_name
    
    new_code = get_code(root)
    return new_code.splitlines(keepends=True)

if __name__ == '__main__':
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = rename_variable(c_file, info={"project": 'tests/testbed'})
    import difflib
    print(''.join(difflib.unified_diff(old_lines, new_lines)))


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
    
    new_name = words.get_random_word()
    while '-' in new_name:
        new_name = words.get_random_word()

    import random
    typename, value = random.choice([
        ('int', '123'),
        ('char', 'a'),
        ('char *', '"hello"'),
    ])

    with open(c_file) as f:
        lines = f.readlines()
    indent = lines[target_idx][:-len(lines[target_idx].lstrip())]
    lines.insert(target_idx, f'{indent}{typename} {new_name} = {value};\n')
    return lines

if __name__ == '__main__':
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = insert_noop(c_file, info={"project": c_file.parent})
    print(''.join(difflib.unified_diff(old_lines, new_lines)))


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
        if et.QName(node).localname == 'case' or et.QName(node).localname == 'default':
            cases.append(node)
            cases_key = tuple(copy.deepcopy(cases))
        else:
            if cases_key not in stmts_by_case:
                stmts_by_case[cases_key] = []
            stmts_by_case[cases_key].append(node)
            if et.QName(node).localname in ['break', 'return']:
                cases = []

    # All blocks of executable statements must end with a "break;"
    for cases, stmts in stmts_by_case.items():
        tag_name = et.QName(stmts[-1]).localname
        if tag_name == 'break':
            stmts.pop()
        elif tag_name == 'return':
            pass
        else:
            raise

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
    narrow_ws = get_space(xp(switch, './src:condition')[0], 'back')
    wide_ws = get_space(xp(switch, './src:block/src:block_content')[0], 'front')
    condition_variable = copy.deepcopy(xp(switch, './src:condition/src:expr')[0])
    condition_variable.tail = '\n'
    IF, ELIF, ELSE = range(3)  # Type of conditional to generate

    def gen_conditional(cases, stmts, if_type):
        """Generate and return a conditional (if/elif/else for a switch case)"""

        if if_type in [IF, ELIF]:
            # Generate a boolean condition expression or'ing together all cases
            sub_exprs = []
            for i, case in enumerate(cases):
                if et.QName(case).localname == 'case':
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
        if any(et.QName(c).localname == 'default' for c in cases):
            default = items.pop(i)
            items.append(default)
            break
    for i, (cases, stmts) in enumerate(items):
        ifs.append(narrow_ws)
        if any(et.QName(c).localname == 'default' for c in cases):
            ifs.append(gen_conditional(cases, stmts, ELSE))
        elif i == 0:
            ifs.append(gen_conditional(cases, stmts, IF))
        else:
            ifs.append(gen_conditional(cases, stmts, ELIF))
    if_stmt = E.if_stmt(*ifs, narrow_ws)
    return if_stmt

def switch_exchange(c_file, picker=lambda i: i[0], info=None):
    root = get_xml_from_file(c_file)
    all_switches = xp(root, f'//src:switch')
    if len(all_switches) == 0:
        return None
    target = picker(all_switches)
    if_stmt = gen_if_stmt(target)
    target.getparent().replace(target, if_stmt)
    return root

if __name__ == '__main__':
    c_file = Path('tests/testbed/testbed.c')
    root = switch_exchange(c_file)
    new_lines = get_code(root).splitlines(keepends=True)
    print(''.join(difflib.unified_diff(old_lines, new_lines)))


# In[111]:


# Refactoring: exchange for loop with while

import re
def loop_exchange(c_file, picker=lambda i: i[0], info=None):
    if len(all_loops) == 0:
        return None
    loop = picker(all_loops)
    
    # Deconstruct loop control node
    loop_control = xp(loop, './src:control')[0]
    init, cond, incr = loop_control
    init = init[0]  # "int i = 0"
    cond = cond[0]  # "i < n"
    incr = incr[0]  # "i ++"
    init.tail = ';\n'
    cond.tail = '\n'

    # Insert loop initializer
    loop_parent.insert(loop_idx, init)
    
    # Insert increment statement
    incr_stmt = E.expr_stmt(incr)
    # whitespace_before_content = get_space(block_content, 'front')
    # Adjust whitespace of the increment statement and the last line in the block
    # block_content[-1].tail, incr_stmt.tail = whitespace_before_content, ';' + block_content[-1].tail
    incr_stmt.tail = ';\n'
    block_content.insert(len(block_content)+1, incr_stmt)

    # Need to add curly braces if the loop doesn't have them
    if block.text is None or '{' in block.text:
        block.text = '{'
        block_content.tail = '}'

    # Replace for loop with while inplace (preserves most whitespace automatically)
    loop.tag = f'{{{namespaces["src"]}}}while'
    loop.text = 'while '
    loop.replace(loop_control, E.condition('(', cond, ')'))
    return root

if __name__ == '__main__':
    c_file = Path('tests/testbed/testbed.c')
    root = loop_exchange(c_file)
    new_lines = get_code(root).splitlines(keepends=True)
    print(''.join(difflib.unified_diff(old_lines, new_lines)))


# In[ ]:




