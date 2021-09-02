import difflib
from pathlib import Path

from refactorings import *
from refactorings.bad_node_exception import BadNodeException
import datetime


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

def diff_lines(old_lines, new_lines):
    """Print the diff between two sets of lines"""
    return list(difflib.unified_diff(old_lines, new_lines))

def print_diff(old_lines, new_lines):
    print(''.join(diff_lines(old_lines, new_lines)))


import pytest

@pytest.mark.parametrize("input_file,expected", [
    ('tests/unit/loop_exchange.c', (3, 1)),
    ('tests/unit/loop_exchange_no_init.c', (2, 1)),
    ('tests/unit/loop_exchange_no_cond.c', (3, 1)),
    ('tests/unit/loop_exchange_no_post.c', (2, 1)),
    ('tests/unit/loop_exchange_empty.c', (1, 1)),
])
def test_loop_exchange_unit(input_file, expected):
    c_file = Path(input_file)
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = LoopExchange(c_file).run()
    assert count_diff(old_lines, new_lines) == expected, print_diff(old_lines, new_lines)

@pytest.mark.parametrize("c_file", [
    'tests/acceptance/loop_exchange/chrome_debian/18159_0.c',  # Unexpected loop subtree structure
    'tests/acceptance/loop_exchange/chrome_debian/4201_0.c',  # Node 178 should have type Condition but has type ForInit
    'tests/acceptance/loop_exchange/chrome_debian/5919_0.c',# Loop does not qualify because its last statement has insufficient location info
])
def test_loop_exchange_acceptance(c_file):
    c_file = Path(c_file)
    diff_file = c_file.with_suffix('.patch')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = LoopExchange(c_file).run()
    diff_out = diff_lines(old_lines, new_lines)
    with open(diff_file) as f:
        diff_exp = f.readlines()
        failed_file = diff_file.with_suffix(f'.fail_{datetime.datetime.now().strftime("%m-%d-%y_%H-%M-%S")}.patch')
        try:
            assert [l.strip() for l in diff_exp] == [l.strip() for l in diff_out]
        except AssertionError:
            print(f'Printing expected -> output failed diff to {failed_file}.')
            with open(failed_file, 'w') as f:
                f.writelines(diff_out)
            raise

@pytest.mark.parametrize("input_file,expected", [
    ('tests/unit/switch_exchange.c', (8, 8)),
    ('tests/unit/switch_exchange_default_not_last.c', 'default in the middle of a switch'),
    ('tests/unit/switch_exchange_fallthrough.c', 'expected BreakStatement but got ExpressionStatement'),
    ('tests/unit/switch_exchange_empty.c', 'empty switch statement'),
])
def test_switch_exchange(input_file, expected):
    c_file = Path(input_file)
    with open(c_file) as f:
        old_lines = f.readlines()
    r = SwitchExchange(c_file)
    all_targets = r.get_targets()
    target = all_targets[0]
    if isinstance(expected, str):
        # Expect fail with message
        with pytest.raises(BadNodeException, match=expected):
            r.run_target(target)
    else:
        new_lines = r.run_target(target)
        assert count_diff(old_lines, new_lines) == expected, print_diff(old_lines, new_lines)

"""
Old tests
"""

def test_permute_stmt():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = PermuteStmt(c_file).run()
    assert count_diff(old_lines, new_lines) == (1, 1)

    c_file = Path('tests/abm/594/nonul2.c')
    # Should only be 1 independent pair
    new_lines = PermuteStmt(c_file).run()

    c_file = Path('tests/ctestsuite/111/fmt_string_local_container.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = PermuteStmt(c_file).run()
    assert new_lines is None, print_diff(old_lines, new_lines)

    c_file = Path('tests/ctestsuite/199/lock_resource.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = PermuteStmt(c_file).run()
    assert count_diff(old_lines, new_lines) == (2, 2), print_diff(old_lines, new_lines)


def test_rename_variable():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = RenameVariable(c_file).run()
    assert count_diff(old_lines, new_lines) == (5, 5)


def test_avoid():
    """Should avoid renaming x and instead rename y (second choice)."""
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = RenameVariable(c_file, avoid_lines=[57]).run()
    assert count_diff(old_lines, new_lines) == (7, 7)


def test_insert_noop():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = InsertNoop(c_file).run()
    assert count_diff(old_lines, new_lines) == (1, 0)


@pytest.mark.skip("outdated")
def test_switch_exchange_old():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = SwitchExchange(c_file).run()
    assert count_diff(old_lines, new_lines) == (4, 10)


@pytest.mark.skip("outdated")
def test_switch_exchange_avoid():
    c_file = Path('tests/testbed/testbed.c')
    new_lines = list(SwitchExchange(c_file).run())
    new_lines2 = list(SwitchExchange(c_file, avoid_lines=[43]).run())
    assert new_lines == new_lines2  # Should be the same
    new_lines3 = SwitchExchange(c_file, avoid_lines=[42]).run()
    assert new_lines3 is None  # Should only be one opportunity for switch exchange, which is excluded

@pytest.mark.skip("outdated")
def test_loop_exchange():
    c_file = Path('tests/testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = LoopExchange(c_file, picker=lambda x: x[0]).run()
    print_diff(old_lines, new_lines)
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = LoopExchange(c_file, picker=lambda x: x[1]).run()
    assert count_diff(old_lines, new_lines) == (3, 1)
    new_lines = LoopExchange(c_file, picker=lambda x: x[2]).run()
    assert count_diff(old_lines, new_lines) == (4, 1)

    c_file = Path('tests/abm/575/into3.c')
    new_lines = LoopExchange(c_file).run()
    assert count_diff(old_lines, new_lines) == (5, 2)

    c_file = Path('tests/ctestsuite/153/os_cmd_loop.c')
    with pytest.raises(Exception, match='insufficient location info'):
        new_lines = LoopExchange(c_file).run()

    c_file = Path('tests/crlf/crlf.c')
    with pytest.raises(Exception, match='CRLF'):
        new_lines = LoopExchange(c_file).run()

    c_file = Path('tests/ctestsuite/125/heap_overflow_cplx.c')
    new_lines = LoopExchange(c_file).run()
    assert count_diff(old_lines, new_lines) == (2, 1)

@pytest.mark.skip("outdated")
def test_loop_badnode():
    c_file = Path('tests/ctestsuite/107/dble_free_local_flow.c')
    assert LoopExchange(c_file).run() is None

@pytest.mark.skip("outdated")
def test_switch_avoid_strip():
    """
    In this case, the lines to avoid (62) is formatted by clang-format, even though the text is not changed by the refactoring.
    This test checks that we are ignoring whitespace on either side of each line.
    """
    c_file = Path('tests/ctestsuite/107/dble_free_local_flow.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = SwitchExchange(c_file, avoid_lines=[62]).run()
    assert count_diff(old_lines, new_lines) == (11, 14)

@pytest.mark.skip("outdated")
def test_project():
    c_file = Path('tests/testbed/testbed.c')
    factory = TransformationsFactory(transforms=all_refactorings, picker=first_picker)
    with factory.make_project(c_file) as project:
        new_filename = project.apply_all()
        with open(c_file) as f:
            old_lines = f.readlines()
        with open(new_filename) as f:
            new_lines = f.readlines()
        assert count_diff(old_lines, new_lines) == (13, 16)
