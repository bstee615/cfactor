from refactorings.insert_noop import insert_noop
from refactorings.rename_variable import rename_variable
from refactorings.permute_stmt import permute_stmt
from refactorings.switch_exchange import switch_exchange
from refactorings.loop_exchange import loop_exchange

from pathlib import Path
import difflib
import pytest


def count_diff(old_lines, new_lines):
    """Count the number of additions and removals between two sets of lines"""
    plus = 0
    minus = 0
    diff_lines = difflib.ndiff(old_lines, new_lines)
    for l in diff_lines:
        if l.startswith('+'):
            plus += 1
        if l.startswith('-'):
            minus += 1
    return plus, minus


def print_diff(old_lines, new_lines):
    """Print the diff between two sets of lines"""
    print(''.join(difflib.unified_diff(old_lines, new_lines)))


def test_permute_stmt():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = permute_stmt(c_file, info={"project": 'tests/testbed', "exclude": None})
    assert count_diff(old_lines, new_lines) == (1, 1)

    c_file = Path('tests/abm/594/nonul2.c')
    # Should only be 1 independent pair
    new_lines = permute_stmt(c_file, info={"project": 'tests/abm/594', "exclude": None})

    c_file = Path('tests/ctestsuite/111/fmt_string_local_container.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = permute_stmt(c_file, info={"project": 'tests/ctestsuite/111', "exclude": None})
    assert new_lines is None, print_diff(old_lines, new_lines)

    c_file = Path('tests/ctestsuite/199/lock_resource.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = permute_stmt(c_file, info={"project": 'tests/ctestsuite/199', "exclude": None})
    assert count_diff(old_lines, new_lines) == (2, 2), print_diff(old_lines, new_lines)


def test_rename_variable():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = rename_variable(c_file, info={"project": 'tests/testbed', "exclude": None})
    assert count_diff(old_lines, new_lines) == (5, 5)


def test_insert_noop():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = insert_noop(c_file, info={"project": c_file.parent, "exclude": None})
    assert count_diff(old_lines, new_lines) == (1, 0)


def test_switch_exchange():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = switch_exchange(c_file)
    assert count_diff(old_lines, new_lines) == (17, 9)


def test_loop_exchange():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, picker=lambda x: x[0], info={
                              "project": c_file.parent, "exclude": None})
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = loop_exchange(c_file, picker=lambda x: x[1], info={
                              "project": c_file.parent, "exclude": None})
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = loop_exchange(c_file, picker=lambda x: x[2], info={
                              "project": c_file.parent, "exclude": None})
    assert count_diff(old_lines, new_lines) == (4, 1)

    c_file = Path('tests/abm/575/into3.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, info={"project": c_file.parent, "exclude": None})
    assert count_diff(old_lines, new_lines) == (5, 2)

    c_file = Path('tests/ctestsuite/153/os_cmd_loop.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    with pytest.raises(Exception, match='insufficient location info'):
        new_lines = loop_exchange(c_file, info={"project": c_file.parent, "exclude": None})

    c_file = Path('tests/crlf/crlf.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    with pytest.raises(Exception, match='CRLF'):
        new_lines = loop_exchange(c_file, info={"project": c_file.parent, "exclude": None})

    c_file = Path('tests/ctestsuite/125/heap_overflow_cplx.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, info={"project": c_file.parent, "exclude": None})
    assert count_diff(old_lines, new_lines) == (2, 1)

def test_project():
    import refactorings
    c_file = Path('tests/testbed/testbed.c')
    default_transforms = (
        refactorings.insert_noop,
        refactorings.switch_exchange,
        refactorings.loop_exchange,
        refactorings.rename_variable,
        refactorings.permute_stmt,
    )
    factory = refactorings.TransformationsFactory(transforms=default_transforms, picker=lambda a: a[0], num_iterations=5)
    with factory.make_project(c_file) as project:
        new_filename = project.apply_all()
        with open(c_file) as f:
            old_lines = f.readlines()
        with open(new_filename) as f:
            new_lines = f.readlines()
        assert count_diff(old_lines, new_lines) == (13, 16)
