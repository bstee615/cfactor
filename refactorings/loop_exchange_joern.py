"""Loop exchange: exchange for loop with while"""

from refactorings.bad_node_exception import BadNodeException
from refactorings.base import BaseTransformation, JoernTransformation
from refactorings.joern import JoernLocation
import re


class LoopExchangeJoernVersion(JoernTransformation):
    def get_targets(self):
        return [n for n, d in self.joern.ast.nodes.items() if d["type"] == 'ForStatement']

    def _apply(self, target):
        succ = list(self.joern.ast.successors(target))
        def pop_node(nodes, node_type):
            found = next((n for n in nodes if self.joern.node_type[n] == node_type), None)
            if found is not None:
                nodes.remove(found)
            return found
        stmt = succ.pop()
        assert self.joern.node_type[stmt].endswith('Statement')
        init = pop_node(succ, 'ForInit')
        cond = pop_node(succ, 'Condition')
        post = succ.pop() if len(succ) > 0 else None
        if post is not None:
            assert self.joern.node_type[post].endswith('Expression'), f'post (located at {self.joern.node_location[post]}) should be of some Expression type but is actually {self.joern.node_type[post]}'
        if stmt is None:
            raise BadNodeException(f'Loop at location {self.joern.node_location[target]} has no body')
        stmt_is_compound = self.joern.node_type[stmt] == 'CompoundStatement'

        # Get locations
        loop_loc = self.joern.node_location[target]
        stmt_loc = self.joern.node_location[stmt]

        # Get the correct whitespace to indent the loop and the body
        loop_indent = self.get_indent(self.old_lines[loop_loc.line-1])
        if stmt_is_compound:
            stmt_first_line_begin = stmt_loc.offset + self.old_text[stmt_loc.offset:].find('\n') + 1
            stmt_first_line_end = stmt_first_line_begin + self.old_text[stmt_first_line_begin:].find('\n')
            body_indent = self.get_indent(self.old_text[stmt_first_line_begin:stmt_first_line_end])
        else:
            body_indent = self.get_indent(self.old_lines[stmt_loc.line-1])

        # Replace for loop with while (try to preserve whitespace before/after the loop, no guarantees about inside the loop)
        new_text = self.old_text[:loop_loc.offset]

        # Add init
        if init is not None:
            init_code = self.joern.node_code[init].strip()
            init_code = '; '.join(c.strip() for c in re.split(r',|;', init_code) if len(c.strip()) > 0)
            new_text += init_code + ';\n' + loop_indent

        # Add loop header
        if cond is None:
            cond_code = 'true'  # Empty condition is equivalent to while(true) (source: https://en.cppreference.com/w/cpp/language/for)
        else:
            cond_code = self.joern.node_code[cond].strip()
        new_text += f'while ({cond_code})\n'

        # Get post line to add to loop body if applicable
        if post is None:
            post_line = ''
        else:
            post_code = self.joern.node_code[post].strip()
            post_line = body_indent + post_code + ';\n'
        stmt_code = self.old_text[stmt_loc.offset:stmt_loc.end_offset+1].strip()
        # Add loop body
        if stmt_is_compound:
            last_line_offset = stmt_code.rfind('\n')+1
            body_code = stmt_code[:last_line_offset] + post_line + stmt_code[last_line_offset:]
        else:
            body_code = '{' + body_indent + stmt_code + '\n' + post_line + loop_indent + '}'
        new_text += loop_indent + body_code

        # Done replacing, add text immediately following the end of the last statement
        new_text += self.old_text[stmt_loc.end_offset+1:]

        lines = new_text.splitlines(keepends=True)
        return lines
