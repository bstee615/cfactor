from refactorings.insert_noop import insert_noop
from refactorings.rename_variable import rename_variable
from refactorings.permute_stmt import permute_stmt
from refactorings.switch_exchange import switch_exchange
from refactorings.loop_exchange import loop_exchange

from pathlib import Path
import difflib


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


def test_permute_stmt():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = permute_stmt(c_file, info={"project": 'tests/testbed'})
    assert count_diff(old_lines, new_lines) == (1, 1)

    c_file = Path('tests/abm/594/nonul2.c')
    # Should only be 1 independent pair
    new_lines = permute_stmt(c_file, info={"project": 'tests/abm/594'})


def test_rename_variable():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = rename_variable(c_file, info={"project": 'tests/testbed'})
    assert count_diff(old_lines, new_lines) == (5, 5)


def test_insert_noop():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = insert_noop(c_file, info={"project": c_file.parent})
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
                              "project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = loop_exchange(c_file, picker=lambda x: x[1], info={
                              "project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = loop_exchange(c_file, picker=lambda x: x[2], info={
                              "project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (4, 1)

    c_file = Path('tests/ctestsuite/069/into2.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, info={"project": c_file.parent})
    assert count_diff(old_lines, new_lines) == (5, 2)

    c_file = Path('tests/abm/575/into3.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = loop_exchange(c_file, info={"project": c_file.parent})

    c_file = Path('tests/crlf/crlf.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    with pytest.raises(Exception, match='CRLF'):
        new_lines = loop_exchange(c_file, info={"project": c_file.parent})
