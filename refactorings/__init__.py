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

from refactorings.insert_noop import InsertNoop
from refactorings.rename_variable import RenameVariable
from refactorings.permute_stmt import PermuteStmt
from refactorings.switch_exchange import SwitchExchange
from refactorings.loop_exchange import LoopExchange
from refactorings.project import TransformationsFactory
import random
import sys

all_refactorings = [
    RenameVariable,
    SwitchExchange,
    LoopExchange,
    PermuteStmt,
    InsertNoop,
]

def random_picker(targets):
    assert len(targets) > 0, 'Collection is empty'
    return random.choice(targets)

def first_picker(targets):
    assert len(targets) > 0, 'Collection is empty'
    return targets[0]

debug = False
if debug:
    print(f'Loaded ({[r.__name__ for r in all_refactorings]})', file=sys.stderr)
    print(f'Loaded {TransformationsFactory.__name__}', file=sys.stderr)
