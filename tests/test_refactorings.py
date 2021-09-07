from pathlib import Path

import pytest
from refactorings import *
from refactorings.bad_node_exception import BadNodeException

from tests.test_utils import test_data_root, print_diff, count_diff


@pytest.mark.parametrize("input_file,expected", [
    (test_data_root/'unit/loop_exchange.c', (3, 1)),
    (test_data_root/'unit/loop_exchange_no_init.c', (2, 1)),
    (test_data_root/'unit/loop_exchange_no_cond.c', (3, 1)),
    (test_data_root/'unit/loop_exchange_no_post.c', (2, 1)),
    (test_data_root/'unit/loop_exchange_empty.c', (1, 1)),
])
def test_loop_exchange_unit(input_file, expected):
    c_file = Path(input_file)
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = LoopExchange(c_file).run()
    assert count_diff(old_lines, new_lines) == expected, print_diff(old_lines, new_lines)

@pytest.mark.parametrize("input_file,expected", [
    (test_data_root/'unit/switch_exchange.c', (8, 8)),
    (test_data_root/'unit/switch_exchange_default_not_last.c', 'default in the middle of a switch'),
    (test_data_root/'unit/switch_exchange_fallthrough.c', 'expected BreakStatement but got ExpressionStatement'),
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
        assert count_diff(old_lines, new_lines) == expected, print_diff(old_lines, new_lines)

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


def test_joern_vs_srcml():
    c_file = Path(test_data_root / 'timing/variables.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    import time
    from refactorings.rename_variable_joern import RenameVariableJoernVersion

    n_trials = 25

    srcml_times = []
    for i in range(n_trials):
        begin = time.time()
        new_lines = RenameVariable(c_file).run()
        end = time.time()
        srcml_times.append(end - begin)
        assert count_diff(old_lines, new_lines) == (1, 1)
        old_lines = new_lines

    joern_times = []
    for i in range(n_trials):
        begin = time.time()
        new_lines = RenameVariableJoernVersion(c_file).run()
        end = time.time()
        joern_times.append(end - begin)
        assert count_diff(old_lines, new_lines) == (1, 1)
        old_lines = new_lines

    print(f'{sum(srcml_times)/len(srcml_times):.2f} SrcML {sum(joern_times)/len(joern_times):.2f} joern')


def test_avoid():
    """Should avoid renaming x and instead rename y (second choice)."""
    c_file = Path(test_data_root/'testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = RenameVariable(c_file, avoid_lines=[57]).run()
    assert count_diff(old_lines, new_lines) == (7, 7)


def test_insert_noop():
    c_file = Path(test_data_root/'testbed/testbed.c')
    with open(c_file) as f:
        old_lines = f.readlines()
    new_lines = InsertNoop(c_file).run()
    assert count_diff(old_lines, new_lines) == (1, 0)
