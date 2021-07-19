"""Rename Variable: replace a local variable's name."""

import srcml
from srcml import xp


def rename_variable(c_file, picker=lambda i: i[0], info=None):
    root = srcml.get_xml_from_file(c_file)
    all_names = xp(root, f'//src:function//src:decl_stmt/src:decl/src:name')
    if len(all_names) == 0:
        return None
    target_name_node = picker(all_names)
    old_target_name = target_name_node.text

    new_target_name = 'fungus'

    function_name = xp(
        xp(target_name_node, './ancestor::src:function')[0], './src:name')[0].text
    targets = xp(
        root, f'//src:name[text() = "{old_target_name}"][ancestor::src:function[./src:name[text() = "{function_name}"]]]')
    if len(targets) == 0:
        return None
    for target in targets:
        target.text = new_target_name

    new_code = srcml.get_code(root)
    return new_code.splitlines(keepends=True)
