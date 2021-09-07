import copy
import logging

from refactorings import RenameVariable, SwitchExchange, LoopExchange, PermuteStmt, InsertNoop
from refactorings.defaults import first_picker

logger = logging.getLogger(__name__)

all_refactorings = [
    RenameVariable,
    SwitchExchange,
    LoopExchange,
    PermuteStmt,
    InsertNoop,
]


class TransformationProject:
    logger = logger

    def __init__(self, c_filename, c_code, transforms=None, picker=first_picker, avoid=None):
        if transforms is None:
            transforms = all_refactorings
        self.transforms = copy.deepcopy(transforms)
        self.picker = picker

        self.c_filename = c_filename
        self.c_code = c_code
        self.avoid = avoid

    def apply_all(self, return_applied=False):
        """Do C source-to-source translation"""

        transformations_applied = []

        # Apply all transforms one at a time
        assert len(self.transforms) > 0, 'empty transform list!'
        while len(self.transforms) > 0:
            if len(self.transforms) == 0:
                self.logger.info('[%s] ran out of transforms', self.c_filename)
                break
            else:
                t = self.transforms[0]

            try:
                new_lines = t(self.c_filename, self.c_code, picker=self.picker, avoid_lines=self.avoid).run()
            except Exception as e:
                self.logger.exception('[%s] exception while applying %s', self.c_filename, t.__name__, exc_info=e)
                self.transforms.remove(t)
                break

            # If it could not be applied, skip this transformation.
            # Most commonly means the transformation had no slot.
            if new_lines is None:
                self.logger.debug('[%s] could not apply %s', self.c_filename, t.__name__)
                self.transforms.remove(t)
                continue
            else:
                # Successfully applied the transformation.
                self.transforms.remove(t)
                transformations_applied.append(t)
                self.logger.debug('[%s] applied %s', self.c_filename, t.__name__)
                self.c_code = ''.join(new_lines)
        if return_applied:
            return self.c_code.splitlines(keepends=True), transformations_applied
        else:
            return self.c_code.splitlines(keepends=True)
