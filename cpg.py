import os, argparse
import networkx as nx
import pandas as pd
import subprocess
from pathlib import Path
import shutil

def gather_stmts(nodes):
    statements = []
    for node in nodes:
        if node["isCFGNode"] == True and node["type"].endswith('Statement') and node["code"]:
            # statements.append((node["type"], node["code"], node["location"]))
            statements.append(node)
    return statements

def parse(project_dir, filepath, exclude):
    # Copy file to tmp directory
    tmp_directory = Path('tmp')
    if tmp_directory.exists():
        shutil.rmtree(tmp_directory)
    os.makedirs(tmp_directory, exist_ok=True)
    dst_dir = tmp_directory / project_dir.name
    assert not dst_dir.exists()
    shutil.copytree(project_dir, dst_dir, ignore=exclude)

    # Invoke joern
    joern_bin = Path('./old-joern/joern-parse')
    joern_parsed = Path('parsed')
    if joern_parsed.exists():
        shutil.rmtree(joern_parsed)
    cmd = f'{joern_bin} {tmp_directory}'
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        print(proc.stdout.decode())
        return

    # Read joern output
    output_path = next((joern_parsed).glob(f'**/{filepath.name}'))
    nodes_path = output_path / 'nodes.csv'
    edges_path = output_path / 'edges.csv'
    nodes_df = pd.read_csv(nodes_path, sep='\t')
    edges_df = pd.read_csv(edges_path, sep='\t')

    # graph_types = [
    #     ('AST', 'IS_AST_PARENT', {"color": 'black'}),
    #     ('CDG', 'CONTROLS', {"color": 'blue'}),
    #     ('DDG', 'REACHES', {"color": 'red'}),
    #     ('CFG', 'FLOWS_TO', {"color": 'blue'}),
    #     ('DFG', 'REACHES', {"color": 'red'}),
    # ]
    # graphs = {}
    cpg = nx.MultiDiGraph()
    nodes_attributes = [{k:v if not pd.isnull(v) else '' for k, v in dict(row).items()} for i, row in nodes_df.iterrows()]
    for na in nodes_attributes:
        na.update({"label": f'{na["key"]}: {na["code"]}'})
    nodes = list(zip(nodes_df["key"].values.tolist(), nodes_attributes))
    cpg.add_nodes_from(nodes)

    # Multigraph
    edges_attributes = [dict(row) for i, row in edges_df.iterrows()]
    edges = list(zip(edges_df["start"].values.tolist(), edges_df["end"].values.tolist(), edges_attributes))
    cpg.add_edges_from(edges)

    # Per type
    # for graph_type, edge_type, extra_edge_attributes in graph_types:
    #     G = nx.DiGraph()
    #     # graphs[graph_type] = G

    #     edge_type_df = edges_df[edges_df["type"] == edge_type]
    #     edges_attributes = [dict(row) for i, row in edge_type_df.iterrows()]
    #     for ea in edges_attributes:
    #         ea.update(extra_edge_attributes)
    #     edges = list(zip(edge_type_df["start"].values.tolist(), edge_type_df["end"].values.tolist(), edges_attributes))
        
    #     G.add_nodes_from(nodes)
    #     G.add_edges_from(edges)
    #     G.remove_nodes_from(list(nx.isolates(G)))
    #     cpg.add_edges_from(edges)

    # print(list(cpg.nodes))
    # print(list(cpg.nodes.values()))
    # stmts = gather_stmts(cpg.nodes.values())
    # for d in stmts:
    #     print(d["key"], d["code"])
    # from networkx.drawing.nx_agraph import write_dot
    # cfg = cpg.edge_subgraph([e for e, d in cpg.edges.items()
    #                       if d["type"] == 'FLOWS_TO']).copy()
    # write_dot(cfg, 'cfg.dot')
    # write_dot(graphs["AST"], 'ast.dot')
    # write_dot(graphs["CDG"], 'cdg.dot')
    # write_dot(graphs["DDG"], 'ddg.dot')

    return cpg

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('code', help='Name of code file')
    args = parser.parse_args()
    code = Path(args.code)
    project_dir = code.parent
    assert code.exists()
    parse(project_dir, code)