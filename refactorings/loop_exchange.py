"""Loop exchange: exchange for loop with while"""

from refactorings.bad_node_exception import BadNodeException
from refactorings.base import BaseTransformation
from refactorings.joern import JoernLocation


class LoopExchange(BaseTransformation):
    def get_targets(self):
        return [n for n, d in self.joern.ast.nodes.items() if d["type"] == 'ForStatement']

    def apply(self, target):
        succ = list(self.joern.ast.successors(target))
        if len(succ) == 4:
            init, cond, post, stmt = succ
            if self.joern.node_type[init] != 'ForInit':
                raise BadNodeException(f'Node {init} should be type ForInit but has type {self.joern.node_type[init]}')
        elif len(succ) == 3:
            init = None
            cond, post, stmt = succ
        else:
            raise BadNodeException('Unexpected loop subtree structure')
        if self.joern.node_type[cond] != 'Condition':
            raise BadNodeException(f'Node {cond} should have type Condition but has type {self.joern.node_type[cond]}')
        if not self.joern.node_type[stmt].endswith('Statement'):
            raise BadNodeException(f'Node {stmt} should be some Statement type but has type {self.joern.node_type[stmt]}')

        # Some statements are disqualified
        janky_location_stmts = (
            'CompoundStatement',
            'IfStatement', 'ElseStatement',
            'ForStatement', 'WhileStatement',
            'SwitchStatement',
        )
        # CompoundStatements don't have reliable code locations,
        # so get the last statement of the loop body
        stmt_is_compound = self.joern.node_type[stmt] == 'CompoundStatement'
        if stmt_is_compound:
            stmt = max(self.joern.g.successors(stmt), key=lambda n: self.joern.node_childNum[n])
            if self.joern.node_type[stmt] in janky_location_stmts:
                raise BadNodeException('Loop does not qualify because its last statement has insufficient location info')
        if not self.joern.node_type[stmt].endswith('Statement'):
            raise BadNodeException('Node {stmt} should be some Statement type but has type {self.joern.node_type[stmt]}')
        
        # Get code and location for the interesting nodes
        cond_code = self.joern.node_code[cond]
        if init is not None:
            init_code = self.joern.node_code[init]
        post_code = self.joern.node_code[post]
        loop_loc = JoernLocation.fromstring(self.joern.node_location[target])
        stmt_loc = JoernLocation.fromstring(self.joern.node_location[stmt])
        
        # Get the correct whitespace to indent the loop and the body
        loop_indent = self.old_lines[loop_loc.line-1][:-len(self.old_lines[loop_loc.line-1].lstrip())]
        body_indent = self.old_lines[stmt_loc.line-1][:-len(self.old_lines[stmt_loc.line-1].lstrip())]

        # Get the last character of the for loop's body
        if stmt_is_compound:
            seek = '}\n'
        else:
            seek = '\n'
        proceed_from = self.old_text.find(seek, stmt_loc.end_offset + 1) + len(seek)

        # Replace for loop with while inplace (preserves most whitespace automatically)
        new_text = self.old_text[:loop_loc.offset]
        if init is not None:
            new_text += init_code + '\n' + loop_indent
        new_text += f'while ({cond_code})'
        if not stmt_is_compound:
            new_text += ' {'
        new_text += self.old_text[loop_loc.end_offset+1:stmt_loc.end_offset+1] + '\n'
        new_text += body_indent + post_code + ';\n'
        new_text += loop_indent + '}\n'
        new_text += self.old_text[proceed_from:]
        lines = new_text.splitlines(keepends=True)
        return lines
