from pathlib import Path

import pytest
from refactorings import *
from refactorings.bad_node_exception import BadNodeException

from tests.test_utils import test_data_root, print_diff, count_diff


@pytest.mark.parametrize("input_file,expected", [
    (test_data_root/'unit/loop_exchange.c', (4, 2)),
    (test_data_root/'unit/loop_exchange_no_init.c', (3, 2)),
    (test_data_root/'unit/loop_exchange_no_cond.c', (4, 2)),
    (test_data_root/'unit/loop_exchange_no_post.c', (3, 2)),
    (test_data_root/'unit/loop_exchange_empty.c', (2, 2)),
])
def test_loop_exchange_unit(input_file, expected):
    c_file = Path(input_file)
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = LoopExchange(c_file).run()
    print_diff(old_lines, new_lines)
    assert count_diff(old_lines, new_lines) == expected

@pytest.mark.parametrize("input_file,expected", [
    (test_data_root/'unit/switch_exchange.c', (7, 7)),
    (test_data_root/'unit/switch_exchange_empty_block.c', (7, 7)),
    (test_data_root/'unit/switch_exchange_comment.c', (7, 7)),
    (test_data_root/'unit/switch_exchange_empty_stmt.c', (7, 7)),
    (test_data_root/'unit/switch_exchange_default_not_last.c', 'fallthrough'),
    (test_data_root/'unit/switch_exchange_fallthrough.c', 'expected tag to end block'),
    (test_data_root/'unit/switch_exchange_empty.c', 'empty switch statement'),
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
        print_diff(old_lines, new_lines)
        assert count_diff(old_lines, new_lines) == expected

"""
Old tests
"""

def test_permute_stmt():
    c_file = Path(test_data_root/'testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = PermuteStmt(c_file).run()
    assert count_diff(old_lines, new_lines) == (1, 1)


def test_rename_variable():
    c_file = Path(test_data_root/'testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = RenameVariable(c_file).run()
    assert count_diff(old_lines, new_lines) == (5, 5)


def test_avoid():
    """Should avoid renaming x and instead rename y (second choice)."""
    c_file = Path(test_data_root/'testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = RenameVariable(c_file, avoid_lines=[57]).run()
    assert count_diff(old_lines, new_lines) == (7, 7)


def test_insert_noop_targetcount():
    c_file = Path(test_data_root/'testbed/testbed.c')
    assert len(InsertNoop(c_file).get_targets()) == 32


def test_insert_noop():
    c_file = Path(test_data_root/'testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = InsertNoop(c_file).run()
    assert count_diff(old_lines, new_lines) == (1, 0)
