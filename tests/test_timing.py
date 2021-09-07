import time
from pathlib import Path

import pytest

import refactorings
from refactorings import RenameVariable, InsertNoop
from refactorings.insert_noop_joern import InsertNoopJoernVersion
from refactorings.rename_variable_joern import RenameVariableJoernVersion
from tests.test_utils import test_data_root, count_diff


@pytest.mark.parametrize("srcml_version,joern_version,filename", [
    (RenameVariable, RenameVariableJoernVersion, 'timing/variables.c'),
    (InsertNoop, InsertNoopJoernVersion, 'timing/noop.c'),
])
def test_joern_vs_srcml(srcml_version, joern_version, filename):
    c_file = Path(test_data_root / filename)
    n_trials = 10

    srcml_times = []
    for i in range(n_trials):
        begin = time.time()
        new_lines = srcml_version(c_file, picker=refactorings.random_picker).run()
        end = time.time()
        srcml_times.append(end - begin)
        # assert count_diff(old_lines, new_lines) == (1, 1)
        old_lines = new_lines

    joern_times = []
    for i in range(n_trials):
        begin = time.time()
        new_lines = joern_version(c_file, picker=refactorings.random_picker).run()
        end = time.time()
        joern_times.append(end - begin)
        # assert count_diff(old_lines, new_lines) == (1, 1)
        old_lines = new_lines

    print(f'{srcml_version.__name__}:{sum(srcml_times)/len(srcml_times):.2f}s')
    print(f'{joern_version.__name__}:{sum(joern_times)/len(joern_times):.2f}s')