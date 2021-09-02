"""Loop exchange: exchange for loop with while"""

from refactorings.base import BaseTransformation
from refactorings.joern import JoernLocation
import re


class LoopExchange(BaseTransformation):
    def get_targets(self):
        return [n for n, d in self.joern.ast.nodes.items() if d["type"] == 'ForStatement']

    def apply(self, target):
        succ = list(self.joern.ast.successors(target))
        if len(succ) == 4:
            init, cond, post, stmt = succ
            assert self.joern.node_type[init] == 'ForInit', f'expected \'ForInit\' got {self.joern.node_type[init]}'
        elif len(succ) == 3:
            init = None
            cond, post, stmt = succ
        else:
            raise Exception('Unexpected loop subtree structure')
        assert self.joern.node_type[cond] == 'Condition'
        assert self.joern.node_type[stmt].endswith('Statement')

        stmt_is_compound = self.joern.node_type[stmt] == 'CompoundStatement'
        
        # Get code and location for the interesting nodes
        loop_loc = JoernLocation.fromstring(self.joern.node_location[target])
        stmt_loc = JoernLocation.fromstring(self.joern.node_location[stmt])
        
        if init is not None:
            init_code = self.joern.node_code[init].strip()
        cond_code = self.joern.node_code[cond].strip()
        stmt_code = self.old_text[stmt_loc.offset:stmt_loc.end_offset+1].strip()
        post_code = self.joern.node_code[post].strip()
        remainder_code = self.old_text[stmt_loc.end_offset+1:].strip()
        
        # Get the correct whitespace to indent the loop and the body
        def get_indent(line):
            return line[:-len(line.lstrip())]
        loop_indent = get_indent(self.old_lines[loop_loc.line-1])
        body_indent = get_indent(self.old_lines[stmt_loc.line-1])

        # Replace for loop with while inplace (preserves most whitespace automatically)
        new_text = self.old_text[:loop_loc.offset]
        if init is not None:
            new_text += init_code + '\n' + loop_indent
        new_text += f'while ({cond_code})'
        if stmt_loc.line == loop_loc.line:
            new_text += ' '
        else:
            new_text += '\n' + {loop_indent}
        if stmt_is_compound:
            last_brace_idx = stmt_code.rfind('}')
            space_idx = last_brace_idx
            while stmt_code[space_idx] != '\n':
                space_idx -= 1
            space_idx += 1
            body_code = stmt_code[:space_idx] + body_indent + post_code + '\n' + loop_indent + stmt_code[last_brace_idx:]
        else:
            body_code = f'''{{
{body_indent}{stmt_code}
{body_indent}{post_code}
{loop_indent}}}\n'''
        new_text += body_code
        new_text += remainder_code
        lines = new_text.splitlines(keepends=True)
        return lines
