from pathlib import Path

from refactorings import LoopExchange, all_refactorings, RenameVariable, SwitchExchange, PermuteStmt, InsertNoop
from tests.test_utils import print_diff

input_file = '../../test.c'
c_file = Path(input_file)
with open(c_file) as f:
    old_code = f.read()

for r in [
    RenameVariable,
    InsertNoop,
    PermuteStmt,
    SwitchExchange,
    LoopExchange,
]:
    old_lines = old_code.splitlines(keepends=True)
    new_lines = r(c_file, old_code).run()
    # print_diff(old_lines, new_lines)
    old_code = ''.join(new_lines)
    print(r.__name__ + ':')
    print(old_code)
