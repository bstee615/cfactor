import os, argparse
import tempfile

import networkx as nx
import pandas as pd
import subprocess
from pathlib import Path
import shutil
import logging

logger = logging.getLogger(__name__)

joern_bin = Path(__file__).parent / 'old-joern/joern-parse'
assert joern_bin.exists(), joern_bin

def gather_stmts(nodes):
    statements = []
    for node in nodes:
        if node["isCFGNode"] == True and node["type"].endswith('Statement') and node["code"]:
            statements.append(node)
    return statements

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.count(os.sep)
        indent = ' ' * 4 * (level)
        logger.debug('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            logger.debug('{}{}'.format(subindent, f))


def parse(filepath):
    # Invoke joern
    joern_dir = filepath.parent.with_suffix('.parsed')
    try:
        cmd = f'bash {joern_bin} {filepath.parent.absolute()} -outdir {joern_dir.absolute()}'
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            logger.error(proc.stdout.decode())

        output_path = joern_dir / str(filepath.absolute())[1:]
        assert output_path.exists(), output_path
        nodes_path = output_path / 'nodes.csv'
        edges_path = output_path / 'edges.csv'
        nodes_df = pd.read_csv(nodes_path, sep='\t')
        edges_df = pd.read_csv(edges_path, sep='\t')
    finally:
        shutil.rmtree(joern_dir)

    cpg = nx.MultiDiGraph()
    nodes_attributes = [{k:v if not pd.isnull(v) else '' for k, v in dict(row).items()} for i, row in nodes_df.iterrows()]
    for na in nodes_attributes:
        na.update({"label": f'{na["key"]} ({na["type"]}): {na["code"]}'}) # Graphviz label

        # Cover fault in Joern exposed by tests/acceptance/loop_exchange/chrome_debian/18159_0.c
        if na["type"].endswith('Statement'):
            with open(filepath) as f:
                file_text = f.read()
            col, line, offset, end_offset = (int(x) for x in na["location"].split(':'))
            if na["type"] == 'CompoundStatement':
                while file_text[offset] != '{':
                    offset -= 1
                while file_text[end_offset] != '}':
                    end_offset += 1
                na["location"] = ':'.join(str(o) for o in (col, line, offset, end_offset))
            elif na["type"] == 'ExpressionStatement':
                if na["code"] == '':
                    pass
                elif na["code"][-1] != ';' and file_text[end_offset] == ';':
                    na["code"] += ';'
    nodes = list(zip(nodes_df["key"].values.tolist(), nodes_attributes))
    cpg.add_nodes_from(nodes)

    # Multigraph
    edges_attributes = [dict(row) for i, row in edges_df.iterrows()]
    edges = list(zip(edges_df["start"].values.tolist(), edges_df["end"].values.tolist(), edges_attributes))
    cpg.add_edges_from(edges)

    return cpg

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('code', help='Name of code file')
    args = parser.parse_args()
    code = Path(args.code)
    project_dir = code.parent
    assert code.exists()
    parse(project_dir, code)
