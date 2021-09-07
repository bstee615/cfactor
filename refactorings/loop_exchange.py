"""Loop exchange: exchange for loop with while"""

from refactorings.bad_node_exception import BadNodeException
from refactorings.base import BaseTransformation, SrcMLTransformation
from refactorings.joern import JoernLocation
import re
from srcml import E


class LoopExchange(SrcMLTransformation):
    def get_targets(self, **kwargs):
        return self.srcml.xp('//src:for')

    def _apply(self, target):
        control = self.srcml.xp(target, 'src:control')[0]
        init = self.srcml.xp(control, 'src:init')[0]
        condition = self.srcml.xp(control, 'src:condition')[0]
        incr = self.srcml.xp(control, 'src:incr')[0]
        block = self.srcml.xp(target, 'src:block')[0]
        insert_idx = target.getparent().index(target)

        try:
            control_tail = control.tail
            control_end = control.getchildren()[-1].tail
            parent = target.getparent()
            parent.remove(target)
            if len(incr) > 0:
                block_content = block.getchildren()[0]
                incr.tail = ';' + block_content.getchildren()[-1].tail
                block_content.getchildren()[-1].tail = block_content.text
                block_content.insert(len(block_content), incr)
            if len(init) > 0:
                init.tail = target.tail
                parent.insert(insert_idx, init)
                insert_idx += 1
            if len(condition) == 0:
                condition.text = None
                for c in condition.getchildren():
                    condition.remove(c)
                literal_true = E.expr(
                    E.literal(
                        '1',
                        {"type": 'number'}
                    )
                )
                condition.insert(0, literal_true)
            condition.text = control.text
            self.srcml.xp(condition, 'src:expr')[0].tail = control_end + control_tail

            new_while_stmt = E(
                'while',
                'while',
                condition,
                block,
                target.tail
            )
            parent.insert(insert_idx, new_while_stmt)
            self.srcml.apply_changes()
        except Exception:
            self.srcml.revert_changes()
            raise

        new_text = self.srcml.load_c_code()
        return new_text.splitlines(keepends=True)
