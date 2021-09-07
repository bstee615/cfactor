
"""Rename Variable: replace a local variable's name."""

from refactorings.base_joern import JoernTransformation
from refactorings.random_word import get_random_word
import networkx.algorithms.dag as nx_algo

class RenameVariableJoernVersion(JoernTransformation):
    def get_targets(self):
        id_decls = [n for n in self.joern.g.nodes() if self.joern.node_type[n] == 'IdentifierDecl']
        all_targets = []
        for d in id_decls:
            children = list(self.joern.ast.successors(d))
            if self.joern.node_type[children[0]] == 'IdentifierDeclType' and self.joern.node_type[children[1]] == 'Identifier':
                all_targets.append(children[1])
        return all_targets

    def _apply(self, target):
        old_target_name = self.joern.node_code[target]
        new_target_name = get_random_word()

        function_def = target
        while self.joern.node_type[function_def] != 'FunctionDef':
            function_def = next(self.joern.ast.predecessors(function_def))
        nodes_in_function = nx_algo.descendants(self.joern.ast, function_def)
        var_refs = [n for n in nodes_in_function
                    if self.joern.node_type[n] == 'Identifier'
                    and self.joern.node_code[n] == old_target_name]
        var_refs = sorted(var_refs, key=lambda n: self.joern.node_location[n].offset)

        assert len(var_refs) > 0, f'no references to variable {old_target_name}'

        new_text = ''
        last_offset = 0
        for v in var_refs:
            loc = self.joern.node_location[v]
            new_text += self.old_text[last_offset:loc.offset]
            new_text += new_target_name
            last_offset = loc.end_offset+1
        new_text += self.old_text[last_offset:]

        return new_text.splitlines(keepends=True)

