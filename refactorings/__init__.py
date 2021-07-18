"""
Semantics preserving transformations modeled after [tnpa-generalizability](https://github.com/mdrafiqulrabin/tnpa-generalizability).
Included:
- Variable Renaming (VN) - renames the name of a variable.
- Permute Statement (PS) - swaps two independent statements in a basic block.
- Unused Statement (UN) - inserts an unused string declaration.
- Loop Exchange (LX) - replaces for loops with while loops or vice versa.
- Switch to If (SF) - replaces a switch statement with an equivalent if statement.
Excluded:
- Boolean Exchange (BX) - switches the value of a boolean variable and propagates this change in the method.
"""

from refactorings.insert_noop import insert_noop
from refactorings.rename_variable import rename_variable
from refactorings.permute_stmt import permute_stmt
from refactorings.switch_exchange import switch_exchange
from refactorings.loop_exchange import loop_exchange

all_refactorings = [
    insert_noop,
    loop_exchange,
    permute_stmt,
    rename_variable,
    switch_exchange,
]

import sys
debug = True
if debug:
    print(f'Loaded ({[r.__name__ for r in all_refactorings]})', file=sys.stderr)