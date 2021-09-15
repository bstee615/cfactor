from pathlib import Path

import pytest

from refactorings import *
from refactorings.bad_node_exception import BadNodeException
from tests.test_utils import test_data_root, print_diff, count_diff


@pytest.mark.parametrize("input_file,expected", [
    (test_data_root / 'unit/loop_exchange.c', (4, 2)),
    (test_data_root / 'unit/loop_exchange_no_init.c', (3, 2)),
    (test_data_root / 'unit/loop_exchange_no_cond.c', (4, 2)),
    (test_data_root / 'unit/loop_exchange_no_post.c', (3, 2)),
    (test_data_root / 'unit/loop_exchange_empty.c', (2, 2)),
    (test_data_root / 'unit/loop_exchange_single_statement.c', (5, 1)),
    (test_data_root / 'unit/loop_exchange_single_statement_no_postincrement.c', (2, 1)),
])
def test_loop_exchange_unit(input_file, expected):
    c_file = Path(input_file)
    with open(c_file) as f:
        old_code = f.read()
        old_lines = old_code.splitlines(keepends=True)
    new_lines = LoopExchange(c_file, old_code).run()
    print_diff(old_lines, new_lines)
    assert count_diff(old_lines, new_lines) == expected


@pytest.mark.parametrize("input_file,expected", [
    (test_data_root / 'unit/switch_exchange.c', (7, 7)),
    (test_data_root / 'unit/switch_exchange_empty_block.c', (7, 7)),
    (test_data_root / 'unit/switch_exchange_comment.c', (7, 7)),
    (test_data_root / 'unit/switch_exchange_empty_stmt.c', (7, 7)),
    (test_data_root / 'unit/switch_exchange_default_not_last.c', 'fallthrough'),
    (test_data_root / 'unit/switch_exchange_fallthrough.c', 'expected tag to end block'),
    (test_data_root / 'unit/switch_exchange_empty.c', 'empty switch statement'),
])
def test_switch_exchange(input_file, expected):
    c_file = Path(input_file)
    with open(c_file) as f:
        old_code = f.read()
        old_lines = old_code.splitlines(keepends=True)
    r = SwitchExchange(c_file, old_code)
    all_targets = r.get_targets()
    target = all_targets[0]
    if isinstance(expected, str):
        # Expect fail with message
        with pytest.raises(BadNodeException, match=expected):
            r.run_target(target)
    else:
        new_lines = r.run_target(target)
        print_diff(old_lines, new_lines)
        assert count_diff(old_lines, new_lines) == expected


"""
Old tests
"""


def test_permute_stmt():
    c_file = Path(test_data_root / 'testbed/testbed.c')
    with open(c_file) as f:
        old_code = f.read()
        old_lines = old_code.splitlines(keepends=True)
    new_lines = PermuteStmt(c_file, old_code).run()
    print_diff(old_lines, new_lines)
    assert count_diff(old_lines, new_lines) == (1, 1)


def test_rename_variable():
    c_file = Path(test_data_root / 'testbed/testbed.c')
    with open(c_file) as f:
        old_code = f.read()
        old_lines = old_code.splitlines(keepends=True)
    new_lines = RenameVariable(c_file, old_code).run()
    assert count_diff(old_lines, new_lines) == (5, 5)


@pytest.mark.skip
def test_avoid():
    """Should avoid renaming x and instead rename y (second choice)."""
    c_file = Path(test_data_root / 'testbed/testbed.c')
    with open(c_file) as f:
        old_code = f.read()
        old_lines = old_code.splitlines(keepends=True)
    new_lines = RenameVariable(c_file, old_code, avoid_lines=[57]).run()
    assert count_diff(old_lines, new_lines) == (7, 7)


def test_insert_noop_targetcount():
    c_file = Path(test_data_root / 'testbed/testbed.c')
    assert len(InsertNoop(c_file, open(c_file).read()).get_targets()) == 32


@pytest.mark.skip('Used for debugging only')
def test_helper():
    c_file = Path('../../data/chrome_debian/raw_code/43_0.c')
    test_transform = LoopExchange
    with open(c_file) as f:
        old_code = f.read()
        old_lines = old_code.splitlines(keepends=True)
    t = test_transform(c_file, old_code, picker=functools.partial(n_picker, n=2))
    new_lines = t.run()
    print_diff(old_lines, new_lines)


def test_preprocessor_failure_throws_happily():
    # This file has a preprocessor directive in a switch case statement which makes parsing fail to recognize the switch label.
    # Make sure it fails with an assertion and not an opaque runtime error.
    c_file = Path(test_data_root / 'acceptance/misc/chrome_debian_17937_0.c')
    with open(c_file) as f:
        old_code = f.read()
    t = SwitchExchange(c_file, old_code)
    new_lines = t.run()
    assert new_lines is None, 'refactoring should fail'


def test_insert_noop():
    c_file = Path(test_data_root / 'testbed/testbed.c')
    with open(c_file) as f:
        old_code = f.read()
        old_lines = old_code.splitlines(keepends=True)
    new_lines = InsertNoop(c_file, old_code).run()
    assert count_diff(old_lines, new_lines) == (1, 0)
