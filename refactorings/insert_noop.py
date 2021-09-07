"""Insert Noop: insert a statement that doesn't affect any other variables."""

from refactorings.base import BaseTransformation, SrcMLTransformation
from refactorings.random_word import get_random_word, get_random_typename_value
import string
from srcml import E
from lxml import etree
import logging
logger = logging.getLogger(__name__)

type_to_literaltype = {
    "int": 'number',
    "char": 'char',
    "char *": 'string',
}
tagnames = ['expr_stmt', 'decl_stmt', 'for', 'do', 'while', 'if_stmt', 'switch', 'label']


class InsertNoop(SrcMLTransformation):
    def get_targets(self, **kwargs):
        targets = []
        for tagname in tagnames:
            targets += self.srcml.xp(f'//src:{tagname}')
        return targets

    def _apply(self, target):
        new_name = get_random_word()

        typename, value = get_random_typename_value()
        literaltype = type_to_literaltype[typename]
        new_decl_stmt = E.decl_stmt(
            E.decl(
                E.type(
                    E.name(typename, ' '),
                    E.name(new_name, ' '),
                    E.init(
                        '= ',
                        E.expr(
                            E.literal(value, {"type": literaltype})
                        )
                    ),
                ),
                ';'
            ),
            target.tail
        )
        logger.debug(etree.tostring(new_decl_stmt))

        try:
            target_idx = target.getparent().index(target)
            target.getparent().insert(target_idx+1, new_decl_stmt)
            self.srcml.apply_changes()
        except Exception:
            self.srcml.revert_changes()
            raise

        new_text = self.srcml.load_c_code()
        return new_text.splitlines(keepends=True)
