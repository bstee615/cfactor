"""Rename Variable: replace a local variable's name."""

import srcml
from srcml import xp
from refactorings.base import BaseTransformation
from refactorings.random_word import get_random_word

class RenameVariable(BaseTransformation):
    def get_targets(self):
        all_names = xp(self.srcml_root, f'//src:function//src:decl_stmt/src:decl/src:name')
        return all_names

    def apply(self, target):
        old_target_name = target.text
        new_target_name = get_random_word()

        function_name = xp(
            xp(target, './ancestor::src:function')[0], './src:name')[0].text
        var_refs = xp(
            self.srcml_root, f'//src:name[text() = "{old_target_name}"][ancestor::src:function[./src:name[text() = "{function_name}"]]]')
        if len(var_refs) == 0:
            return None
        for target in var_refs:
            target.text = new_target_name

        new_code = srcml.get_code(self.srcml_root)
        return new_code.splitlines(keepends=True)
