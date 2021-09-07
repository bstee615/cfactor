import datetime
from pathlib import Path

import pytest

from refactorings import *
from refactorings.project import TransformationProject
from tests.test_utils import test_data_root, diff_lines, print_diff, count_diff

"""
Acceptance tests
"""


@pytest.mark.parametrize("c_file", [
    test_data_root / 'acceptance/loop_exchange/chrome_debian/18159_0.c',  # Unexpected loop subtree structure
    test_data_root / 'acceptance/loop_exchange/chrome_debian/4201_0.c',
    # Node 178 should have type Condition but has type ForInit
    test_data_root / 'acceptance/loop_exchange/chrome_debian/5919_0.c',
    # Loop does not qualify because its last statement has insufficient location info
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


def test_project():
    c_file = Path(test_data_root / 'testbed/testbed.c')
    with TransformationProject(c_file, transforms=all_refactorings, picker=first_picker) as project:
        new_filename = project.apply_all()
        with open(c_file) as f:
            old_lines = f.readlines()
        with open(new_filename) as f:
            new_lines = f.readlines()
        print_diff(old_lines, new_lines)
        assert count_diff(old_lines, new_lines) == (16, 19), print_diff(old_lines, new_lines)


def test_crlf():
    c_file = Path(test_data_root / 'crlf/crlf.c')
    with pytest.raises(Exception, match='.* is CRLF'):
        PermuteStmt(c_file).run()
