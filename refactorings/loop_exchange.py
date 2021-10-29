"""Loop exchange: exchange for loop with while"""
import copy

from refactorings.bad_node_exception import BadNodeException
from refactorings.base import SrcMLTransformation
from refactorings.util import join_str
from srcml import E


class LoopExchange(SrcMLTransformation):
    def get_targets(self, **kwargs):
        return self.srcml.xp('//src:for')

    def _apply(self, target):
        try:
            control = self.srcml.xp(target, 'src:control')[0]
            init = self.srcml.xp(control, 'src:init')[0]
            condition = self.srcml.xp(control, 'src:condition')[0]
            incr = self.srcml.xp(control, 'src:incr')[0]
            block = self.srcml.xp(target, 'src:block')[0]
        except IndexError:
            raise BadNodeException('for loop is not well-formed')
        insert_idx = target.getparent().index(target)

        try:
            control_tail = control.tail
            control_end = control.getchildren()[-1].tail
            parent = target.getparent()
            parent.remove(target)
            if len(incr) > 0:
                block_content = block.getchildren()[0]
                block_type = block.get('type')
                is_pseudo = block_type is not None and block_type == 'pseudo'
                block_content_children = block_content.getchildren()
                if is_pseudo:
                    block.text = join_str(target.tail, '{')
                    block_content.tail = '}'
                incr.tail = join_str(';', target.tail)
                # Insert increment statement before each continue to fully conform with C spec.
                # https://en.cppreference.com/w/cpp/language/for#:~:text=continue%20in%20the%20statement%20will%20execute%20iteration-expression
                for continue_stmt in self.srcml.xp(block_content, './/src:continue'):
                    continue_parent_stmt = continue_stmt.getparent()
                    incr_copy = copy.deepcopy(incr)
                    incr_copy.tail = join_str(';', continue_parent_stmt.text)
                    continue_parent_stmt.insert(continue_parent_stmt.index(continue_stmt), incr_copy)
                if len(block_content_children) > 0:
                    block_content_children[-1].tail = block_content.text
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
            self.srcml.xp(condition, 'src:expr')[0].tail = join_str(control_end, control_tail)

            args = [
                'while',
                'while',
                condition,
                block
            ]
            if target.tail is not None:
                args.append(target.tail)
            new_while_stmt = E(*args)
            parent.insert(insert_idx, new_while_stmt)
            self.srcml.apply_changes()
        except Exception:
            self.srcml.revert_changes()
            raise

        new_text = self.srcml.load_c_code()
        return new_text.splitlines(keepends=True)
