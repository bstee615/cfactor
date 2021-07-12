#!/usr/bin/env python
# coding: utf-8

# In[109]:


import networkx as nx
from networkx.drawing import nx_pydot
def load_reachable(project, function):
    """Load PDG and return the set of reachable nodes for every nodes"""
    G = nx_pydot.read_dot(f'{project}/cpg/{function}.pdg.dot')
    blacklist = [1000100]  # These are nodes which we shouldn't consider
    reaches = {}  # k reaches all v
    for source, sink_lengths in nx.all_pairs_shortest_path_length(G):
        source = int(source)
        if source not in blacklist:
            reaches[source] = {int(s) for s, l in sink_lengths.items() if (s not in blacklist) and l > 0}
    return reaches

def load_dep(project, function):
    """Load control/data dependencies for every node"""
    reaches = load_reachable(project, function)
    reachable_by = {n:{source for source, sinks in reaches.items() if n in sinks} for n in reaches.keys()}
    return reachable_by

# print(load_dep('assign-test', 'main')[1000115])


# In[142]:


# Load basic blocks
import networkx as nx
from networkx.drawing import nx_pydot
def load_cfg(project, function):
    """Load CFG. Index basic blocks."""
    G = nx_pydot.read_dot(f'{project}/cpg/{function}.cfg.dot')
    # node instanceof ExpressionStmt && node.findAll(MethodCallExpr.class).size() == 0
    q = []
    visited = set()
    q.append(list(G.nodes)[0])
    blocks = []
    b = []
    while len(q) > 0:
        u = q.pop(0)
        n = list(G.neighbors(u))
        if len(n) > 1:
            blocks.append(b)
            b = []
        else:
            b.append(u)
        for v in n:
            if v not in visited:
                visited.add(u)
                q.append(v)
    
    return blocks

# print(load_cfg('loop-test', 'main'))


# In[110]:


import json
def load_ast(project, function):
    """Load Joern AST. It should subsume the PDG."""
    with open(f'{project}/cpg/{function}.ast.json') as f:
        ast = json.load(f)
    ast = {n["id"]:n for n in ast}
    return ast
# print(load_ast('assign-test', 'main')[1000115])


# In[123]:

import os

def load_annotated_ast_nodes(project, function):
    if not os.path.exists(f'{project}/cpg/{function}.ast.json') or not os.path.exists(f'{project}/cpg/{function}.pdg.dot'):
        proc = subprocess.run(['bash', 'joern-util/dump.sh', project, function], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        if proc.returncode != 0:
            print(f'Exit {proc.returncode}. Echoing process output:', proc.stdout.decode('utf-8'))
    ast = load_ast(project, function)
    rdef = load_dep(project, function)

    # Check correctness
    pdg_nodes = set(rdef.keys())
    ast_nodes = {n["id"] for n in ast.values()}
    assert pdg_nodes.issubset(ast_nodes), pdg_nodes.difference(ast_nodes)

    # Annotate AST with reaching definitions
    annotated_ast = {}
    for i, n in ast.items():
        if i in rdef:
            n["dependencies"] = rdef[i]
            annotated_ast[i] = n

    return annotated_ast
# ast = load_annotated_ast_nodes('assign-test', 'main')
# print(len(ast))
# ast[1000115], ast[1000118]


# In[121]:


import subprocess
def getNodeLineNumber(nodes):
    args = 'joern-cli/joern --script joern-util/getMultipleNodesProperty.sc --params'.split()
    args.append(f'project=assign-test,ids={";".join(str(n) for n in nodes)},property=LINE_NUMBER')
    print(' '.join(args))
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout.decode('utf-8'))
def getOneNodeLineNumber(node):
    args = 'joern-cli/joern --script joern-util/getNodePropertySingle.sc --params'.split()
    args.append(f'project=assign-test,id={node},property=LINE_NUMBER')
    print(' '.join(args))
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout.decode('utf-8'))
# getOneNodeLineNumber(1000107)

