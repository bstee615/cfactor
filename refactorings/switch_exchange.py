
# Refactoring: exchange switch with if/else
from collections import OrderedDict
import copy
from refactorings.bad_node_exception import BadNodeException

import srcml
from srcml import prettyprint, xp, E
from refactorings import clang_format
from refactorings.base import BaseTransformation

class SwitchExchange(BaseTransformation):
    def get_stmts_by_case(self, switch):
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
            if srcml.tagname(node) == 'case' or srcml.tagname(node) == 'default':
                cases.append(node)
                cases_key = tuple(copy.deepcopy(cases))
            else:
                if cases_key not in stmts_by_case:
                    stmts_by_case[cases_key] = []
                stmts_by_case[cases_key].append(node)
                if srcml.tagname(node) in ['break', 'return']:
                    cases = []

        # All blocks of executable statements must end with a "break;"
        for cases, stmts in stmts_by_case.items():
            tag_name = srcml.tagname(stmts[-1])
            if tag_name == 'break':
                stmts.pop()
            elif tag_name == 'return':
                pass
            else:
                raise BadNodeException(f'Unknown statement tag ends a switch: {tag_name}')
            for stmt in stmts:
                n = xp(stmt, './/src:break')
                # TODO: Convert these to nested if/else (else block is everything after the condition wrapping the break)
                if n:
                    raise BadNodeException(f'Break occurs in the middle of a switch statement')

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

    def gen_if_stmt(self, switch):
        """Generate a big if_stmt (if/elif/else) from a switch statement"""

        stmts_by_case = self.get_stmts_by_case(switch)
        narrow_ws = srcml.get_space(xp(switch, './src:condition')[0], 'back')
        wide_ws = srcml.get_space(xp(switch, './src:block/src:block_content')[0], 'front')
        condition_variable = copy.deepcopy(xp(switch, './src:condition/src:expr')[0])
        condition_variable.tail = '\n'
        IF, ELIF, ELSE = range(3)  # Type of conditional to generate

        def gen_conditional(cases, stmts, if_type):
            """Generate and return a conditional (if/elif/else for a switch case)"""

            if if_type in [IF, ELIF]:
                # Generate a boolean condition expression or'ing together all cases
                sub_exprs = []
                for i, case in enumerate(cases):
                    if srcml.tagname(case) == 'case':
                        case_value = xp(case, './src:expr')[0]
                        case_value.tail = '\n'
                        sub_expr = E.expr(copy.deepcopy(condition_variable), ' ', E.operator('=='), case_value)
                        sub_exprs.append(sub_expr)
                    if i < len(cases) - 1:
                        sub_exprs.append(E.operator('||'))
                if len(stmts) > 0:
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
            if any(srcml.tagname(c) == 'default' for c in cases):
                default = items.pop(i)
                items.append(default)
                break
        for i, (cases, stmts) in enumerate(items):
            ifs.append(narrow_ws)
            if any(srcml.tagname(c) == 'default' for c in cases):
                ifs.append(gen_conditional(cases, stmts, ELSE))
            elif i == 0:
                ifs.append(gen_conditional(cases, stmts, IF))
            else:
                ifs.append(gen_conditional(cases, stmts, ELIF))
        if_stmt = E.if_stmt(*ifs, narrow_ws)
        return if_stmt

    def get_targets(self):
        all_switches = xp(self.srcml_root, f'//src:switch')
        return all_switches

    def apply(self, target):
        # TODO: filter switches by ones with static expression (no function call).
        if_stmt = self.gen_if_stmt(target)
        target.getparent().replace(target, if_stmt)
        new_lines = srcml.get_code(self.srcml_root).splitlines(keepends=True)
        return clang_format.reformat(self.old_lines, new_lines)
