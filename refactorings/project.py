import copy
import difflib
import logging
import random

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
refactorings_without_new_names = [
    # RenameVariable,
    SwitchExchange,
    LoopExchange,
    PermuteStmt,
    # InsertNoop,
]
# TODO: implement permute_condition, permute_if_else


class TransformationProject:
    logger = logger

    def __init__(self, c_filename, c_code, transforms=None, picker=first_picker, avoid=None, style='one_of_each', style_args=None):
        if transforms is None:
            transforms = all_refactorings
        self.transforms = copy.deepcopy(transforms)
        assert len(self.transforms) > 0, 'empty transform list!'
        self.picker = picker

        self.c_filename = c_filename
        self.original_c_code = self.c_code = c_code
        self.avoid = avoid
        self.style = style
        self.style_info = {"args": style_args}
        self.init_transform()

    def init_transform(self):
        if self.style == 'one_of_each':
            pass
        elif self.style == 'k_random':
            self.style_info["k"] = int(self.style_info["args"][0])
        elif self.style == 'threshold':
            self.style_info["threshold"] = float(self.style_info["args"][0])
            self.style_info["max_stagnant"] = int(self.style_info["args"][1])
            self.style_info["last_num_changed"] = None
            self.style_info["stagnant"] = 0
        del self.style_info["args"]

    def get_transform(self):
        if self.style == 'one_of_each':
            if len(self.transforms) == 0:
                # self.logger.info('[%s] ran out of transforms', self.c_filename)
                return None
            else:
                return self.transforms.pop(0)
        elif self.style == 'k_random':
            if self.style_info["k"] == 0:
                return None
            else:
                self.style_info["k"] -= 1
                return random.choice(self.transforms)
        elif self.style == 'threshold':
            original_code_lines = self.original_c_code.splitlines(keepends=True)
            diff = difflib.ndiff(original_code_lines, self.c_code.splitlines(keepends=True))
            num_changed = len([line for line in diff if line[:2] in ('- ', '+ ')])
            percent_changed = num_changed / len(original_code_lines)
            if percent_changed >= self.style_info["threshold"]:  # If this condition is repeated without num_changed increasing, maybe we should quit with an exception
                return None
            else:
                if self.style_info["last_num_changed"] is not None:
                    if self.style_info["last_num_changed"] == num_changed:
                        self.style_info["stagnant"] += 1
                        if self.style_info["stagnant"] >= self.style_info["max_stagnant"]:
                            # logger.info(f'stagnant for {self.style_info["stagnant"]} tries, quitting at {percent_changed}')
                            return None
                    else:
                        self.style_info["stagnant"] = 0
                self.style_info["last_num_changed"] = num_changed
                return random.choice(self.transforms)
        else:
            raise Exception(f'unknown transform style {self.style}')

    def apply_all(self, return_applied=False):
        """Do C source-to-source translation"""

        transformations_applied = []

        # Apply all transforms one at a time
        t = self.get_transform()
        while t is not None:

            try:
                new_lines = t(self.c_filename, self.c_code, picker=self.picker, avoid_lines=self.avoid).run()
            except Exception as e:
                self.logger.exception('[%s] exception while applying %s', self.c_filename, t.__name__, exc_info=e)
                break

            # If it could not be applied, skip this transformation.
            # Most commonly means the transformation had no slot.
            if new_lines is None:
                self.logger.debug('[%s] could not apply %s', self.c_filename, t.__name__)
            else:
                # Successfully applied the transformation.
                transformations_applied.append(t)
                self.logger.debug('[%s] applied %s', self.c_filename, t.__name__)
                self.c_code = ''.join(new_lines)

            t = self.get_transform()
        if return_applied:
            return self.c_code.splitlines(keepends=True), transformations_applied
        else:
            return self.c_code.splitlines(keepends=True)
