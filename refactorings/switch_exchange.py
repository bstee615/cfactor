
# Refactoring: exchange switch with if/else
from collections import OrderedDict
import copy
from refactorings.bad_node_exception import BadNodeException

import srcml
from srcml import prettyprint, xp, E
from refactorings import clang_format
from refactorings.base import BaseTransformation
from refactorings.joern import JoernLocation
import logging
import re


class SwitchExchange(BaseTransformation):
    logger = logging.getLogger('SwitchExchange')

    def get_targets(self):
        return [n for n, d in self.joern.ast.nodes.items() if d["type"] == 'SwitchStatement']

    def apply(self, target):
        # TODO: filter switches by ones with static expression (no function call).
        cond, compound = self.joern.ast.successors(target)
        children = sorted(self.joern.ast.successors(compound))
        stmts_in_compound = list(children)

        block = []
        block_ender = None
        blocks = []
        while len(children) > 0:
            c = children.pop(0)
            if self.joern.node_type[c] == 'Label':
                if len(block) == 0 or all(self.joern.node_type[n] == 'Label' for n in block):
                    block.append(c)
                else:
                    if block_ender is not None:
                        assert self.joern.node_type[block_ender] == 'BreakStatement'
                    blocks.append(block)
                    block_ender = None
                    block = []
                    block.append(c)
            else:
                block.append(c)
        blocks.append(block)
        self.logger.debug(f'{len(blocks)=}')

        # TODO: check no fall-through using CFG

        def get_indent(line):
            return line[:-len(line.lstrip())]
        def get_location(n):
            return JoernLocation.fromstring(self.joern.node_location[n])
        def get_type(n):
            return self.joern.node_type[n]
        def get_code(n):
            return self.joern.node_code[n]

        target_location = get_location(target)
        switch_indent = get_indent(self.old_lines[target_location.line])
        # Find the first child that isn't a label and get its indentation.
        # If there is none, default to the first label.
        for n in stmts_in_compound:
            first_body_child = n
            if self.joern.node_type[n] != 'Label':
                break
        first_body_child = get_location(first_body_child)
        body_indent = get_indent(self.old_lines[first_body_child.line])

        compound_location = get_location(compound)

        new_text = self.old_text[:target_location.offset]
        # Add in new if/elses
        all_codes = []
        for i, block in enumerate(blocks):
            labels, stmts = [], []
            for n in block:
                if self.joern.node_type[n] == 'Label':
                    labels.append(n)
                elif self.joern.node_type[n] != 'BreakStatement':
                    stmts.append(n)
            self.logger.debug(f'{labels=} {stmts=}')

            # If condition
            def get_if_condition():
                switch_cond_code = get_code(cond)
                label_exprs = []
                for n in labels:
                    label_code = get_code(n)
                    m = re.fullmatch(r'\s*default\s*:', label_code)
                    if m is not None:
                        return 'else'
                    else:
                        m = re.fullmatch(r'\s*case\s*(.*)\s*:', label_code)
                        if m is None:
                            m = re.fullmatch(r'\s*case\s*(.*)\s*:', label_code)
                            raise BadNodeException(f'Could not parse {label_code} for label at location {get_location(n)}')
                        else:
                            label_code = m.group(1)
                            label_exprs.append(label_code.strip())
                cond_expr_code = ' || '.join((f'{switch_cond_code} == {code}') for code in label_exprs)
                if_cond_code = f'if ({cond_expr_code})'
                if i > 0:
                    if_cond_code = 'else ' + if_cond_code
                return if_cond_code
            if_cond_code = get_if_condition()
            self.logger.debug(f'if_cond_code="{if_cond_code}"')

            # Wrap code statements in {}
            # stmts_lines = []
            # for n in stmts:
                # stmt_code = get_code(n)
                # if not stmt_code.rstrip()[-1] not in (';', ')', '}'):
                #     stmt_code += ';'
                # stmts_lines.append(stmt_code)
            stmts_code = ('\n' + body_indent).join(map(get_code, stmts))
            stmts_code = switch_indent + '{\n' + body_indent + stmts_code + '\n' + switch_indent + '}'
            self.logger.debug(f'stmts_code="{stmts_code}"')

            all_code = if_cond_code + '\n' + stmts_code
            self.logger.debug(f'all_code="{all_code}"')
            all_codes.append(all_code)
        new_text += ('\n' + switch_indent).join(all_codes)
        new_text += self.old_text[compound_location.end_offset+1:]

        new_lines = new_text.splitlines(keepends=True)
        return new_lines
