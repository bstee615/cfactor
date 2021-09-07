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
from refactorings.defaults import first_picker, random_picker
from refactorings.project import TransformationProject, all_refactorings

