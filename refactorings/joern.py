import cpg
import networkx as nx
import dataclasses

class JoernInfo:
    def __init__(self, *args):
        self.g = cpg.parse(*args)
        self.ast = self.g.edge_subgraph([e for e, d in self.g.edges.items()
                            if d["type"] == 'IS_AST_PARENT']).copy()
        self.cfg = self.g.edge_subgraph([e for e, d in self.g.edges.items()
                            if d["type"] == 'FLOWS_TO']).copy()
        self.ddg = self.g.edge_subgraph([e for e, d in self.g.edges.items()
                            if d["type"] == 'REACHES']).copy()
        
        self.node_type = nx.get_node_attributes(self.g, 'type')
        self.node_code = nx.get_node_attributes(self.g, 'code')
        self.node_location = {k:JoernLocation.fromstring(v) if v != '' else None for k, v in nx.get_node_attributes(self.g, 'location').items()}
        self.node_childNum = nx.get_node_attributes(self.g, 'childNum')

    def print_dot(self, graph='g'):
        """Convenience function to print the dot representation."""
        dot = nx.nx_pydot.to_pydot(getattr(self, graph))
        print(dot)
        return dot

@dataclasses.dataclass
class JoernLocation:
    line: int  # 1-indexed
    column_idx: int  # All others 0-indexed
    offset: int
    end_offset: int

    @staticmethod
    def fromstring(location):
        return JoernLocation(*map(int, location.split(':')))
