
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
        # case = self.srcml.xp(target, 'src:case')[0]
        block_content = self.srcml.xp(target, 'src:block')[0][0]

        children = list(block_content)
        assert len(children) > 0, 'empty switch statement'

        block = []
        block_ender = None  # Last statement in the block
        blocks = []
        while len(children) > 0:
            c = children.pop(0)
            if self.srcml.tag(c) in ('case', 'default'):
                if len(block) == 0 or all(self.srcml.tag(n) == 'case' for n in block):
                    block.append(c)
                else:
                    if block_ender is not None:
                        # Check that there are no fallthroughs and that last statement is break
                        assert self.srcml.tag(block_ender) in ('break', 'return'),\
                            f'expected tag to end block but got {block_ender.tag}'
                    blocks.append(block)
                    block_ender = None
                    block = [c]
            else:
                block.append(c)
                block_ender = c
        blocks.append(block)
        self.logger.debug(f'{len(blocks)=}')

        try:
            block_content_text = block_content.text
            ifs = []
            cond_expr = self.srcml.xp(cond, 'src:expr')[0]
            cond_expr.tail = ' '
            for i, block in enumerate(blocks):
                is_default = False
                labels, stmts = [], []
                for n in block:
                    if self.srcml.tag(n) == 'default':
                        assert i == len(blocks)-1, 'fallthrough not supported'
                        is_default = True
                        labels.append(n)
                    elif self.srcml.tag(n) == 'case':
                        labels.append(n)
                    elif self.srcml.tag(n) != 'break':
                        stmts.append(n)
                self.logger.debug(f'{labels=} {stmts=}')

                stmts[-1].tail = block_content_text

                if is_default:
                    if_type = 'else'
                    if_text = 'else'
                else:
                    if_type = 'if'
                    if_text = 'if'
                if not is_default and i > 0:
                    if_attrs = {"type": 'elseif'}
                    if_text = 'else if'
                else:
                    if_attrs = {}
                self.logger.debug(f'{if_type=} {if_text=} {if_attrs=}')

                args = [
                    if_type,
                    f'{if_text} ',
                    if_attrs
                ]

                if not is_default:
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

                if i == len(blocks)-1:
                    ender = '}'
                else:
                    ender = '}' + block_content_text
                args.append(E.block(E.block_content(block_content_text + '{' + labels[-1].tail, *stmts, ender)))

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
