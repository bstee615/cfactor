
# Refactoring: exchange switch with if/else
from collections import OrderedDict
import copy
from refactorings.bad_node_exception import BadNodeException

# from refactorings import clang_format
from refactorings.base import BaseTransformation, JoernTransformation, SrcMLTransformation
from refactorings.joern import JoernLocation
import logging
import re
from srcml import E


class SwitchExchange(SrcMLTransformation):
    logger = logging.getLogger('SwitchExchange')

    def get_targets(self, **kwargs):
        return self.srcml.xp('//src:switch')

    def _apply(self, target):
        cond = self.srcml.xp(target, 'src:condition')[0]
        block_content = self.srcml.xp(target, 'src:block')[0][0]

        children = list(block_content)
        assert len(children) > 0, 'empty switch statement'

        # Get all switch blocks
        block = []
        block_ender_ok = True  # Last statement in the block
        blocks = []
        while len(children) > 0:
            c = children.pop(0)
            if self.srcml.tag(c) in ('case', 'default'):
                if len(block) == 0 or all(self.srcml.tag(n) == 'case' for n in block):
                    block.append(c)
                else:
                    assert block_ender_ok, f'expected tag to end block'
                    blocks.append(block)
                    block_ender_ok = True
                    block = [c]
            else:
                block.append(c)
                block_ender_ok = self.srcml.tag(c) in ('break', 'return')
        blocks.append(block)
        self.logger.debug(f'{len(blocks)=}')

        try:
            # Save some nodes
            block_content_text = block_content.text
            cond_expr = self.srcml.xp(cond, 'src:expr')[0]
            cond_expr.tail = ' '

            ifs = []
            for i, block in enumerate(blocks):
                # Dissect block
                block_is_default = False
                labels, stmts = [], []
                for n in block:
                    if self.srcml.tag(n) == 'default':
                        assert i == len(blocks)-1, 'fallthrough not supported'
                        block_is_default = True
                        labels.append(n)
                    elif self.srcml.tag(n) == 'case':
                        labels.append(n)
                    elif self.srcml.tag(n) != 'break':
                        stmts.append(n)
                self.logger.debug(f'{labels=} {stmts=}')

                # Will be used to build arguments for call to E.if_stmt
                args = []

                # Assemble beginning of conditional statement
                if block_is_default:
                    if_type = 'else'
                    if_text = 'else'
                else:
                    if_type = 'if'
                    if_text = 'if'
                if not block_is_default and i > 0:
                    if_attrs = {"type": 'elseif'}
                    if_text = 'else if'
                else:
                    if_attrs = {}
                args += [
                    if_type,
                    f'{if_text} ',
                    if_attrs
                ]
                self.logger.debug(f'{if_type=} {if_text=} {if_attrs=}')

                # Assemble conditional
                if not block_is_default:
                    exprs = []
                    for j, n in enumerate(labels):
                        e = n[0]
                        if j < len(labels)-1:
                            e.tail = ' '
                        else:
                            e.tail = None
                        exprs.append(e)
                    if_cond_expr_contents = []
                    for j, expr in enumerate(exprs):
                        if_cond_expr_contents.append(copy.deepcopy(cond_expr))
                        if_cond_expr_contents.append(E.operator('==', ' '))
                        if_cond_expr_contents.append(expr)
                        if j < len(exprs)-1:
                            if_cond_expr_contents.append(E.operator('||', ' '))
                    args.append(E.condition(
                        '(',
                        E.expr(
                            *if_cond_expr_contents,
                            ')'
                        )
                    ))
                    self.logger.debug(f'conditioning on {len(exprs)} expressions')

                # Assemble block content (statements inside the block)
                if len(stmts) > 0:
                    stmts[-1].tail = block_content_text
                if i == len(blocks)-1:
                    block_content_tail = '}'
                else:
                    block_content_tail = '}' + block_content_text
                args.append(
                    E.block(
                        E.block_content(
                            block_content_text + '{' + labels[-1].tail,
                            *stmts,
                            block_content_tail
                        )
                    )
                )
                self.logger.debug(f'added {len(stmts)} stmts')

                if_part = E(*args)
                ifs.append(if_part)
            if_stmt = E.if_stmt(*ifs)
            if_stmt.tail = target.tail
            parent = target.getparent()
            insert_idx = parent.index(target)
            parent.remove(target)
            parent.insert(insert_idx, if_stmt)
            self.srcml.apply_changes()
        except Exception:
            self.srcml.revert_changes()
            raise

        new_text = self.srcml.load_c_code()
        return new_text.splitlines(keepends=True)
