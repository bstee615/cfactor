"""Insert Noop: insert a statement that doesn't affect any other variables."""

from pathlib import Path
import networkx as nx
import cpg
import random
from refactorings.base import BaseTransformation


class InsertNoop(BaseTransformation):
    def get_targets(self):
        def is_target(n):
            is_valid_stmt = self.joern.node_type[n] in ('ExpressionStatement', 'IfStatement', 'ElseStatement', 'ForStatement', 'WhileStatement')
            has_valid_location = isinstance(self.joern.node_location[n], str)
            pred = list(self.joern.ast.predecessors(n))
            if len(pred) > 0:
                parent_is_compound = self.joern.node_type[pred[0]] == 'CompoundStatement'
            else:
                parent_is_compound = False
            return is_valid_stmt and parent_is_compound and has_valid_location
        return [self.joern.node_location[n] for n in filter(is_target, self.joern.ast.nodes)]

    def apply(self, target):
        target_line = int(target.split(':')[0])
        target_idx = target_line - 1

        new_name = 'mungus'

        typename, value = random.choice([
            ('int', '123'),
            ('char', '\'a\''),
            ('char *', '"hello"'),
        ])

        indent = self.old_lines[target_idx][:-len(self.old_lines[target_idx].lstrip())]
        self.old_lines.insert(target_idx, f'{indent}{typename} {new_name} = {value};\n')
        return self.old_lines
