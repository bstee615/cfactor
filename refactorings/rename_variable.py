"""Rename Variable: replace a local variable's name."""

from refactorings.base import BaseTransformation, SrcMLTransformation
from refactorings.random_word import get_random_word
import networkx.algorithms.dag as nx_algo

class RenameVariable(SrcMLTransformation):
    def get_targets(self):
        all_names = self.srcml.xp(f'//src:function//src:decl_stmt/src:decl/src:name')
        return all_names

    def _apply(self, var_ref):
        old_target_name = var_ref.text
        new_target_name = get_random_word()

        function_name = self.srcml.xp(self.srcml.xp(var_ref, './ancestor::src:function')[0], './src:name')[0].text
        var_refs = self.srcml.xp(f'//src:name[text() = "{old_target_name}"][ancestor::src:function[./src:name[text() = "{function_name}"]]]')
        if len(var_refs) == 0:
            return None

        try:
            for var_ref in var_refs:
                var_ref.text = new_target_name
            self.srcml.apply_changes()
        except Exception:
            self.srcml.revert_changes()
            raise
        new_code = self.srcml.load_c_code()
        return new_code.splitlines(keepends=True)
