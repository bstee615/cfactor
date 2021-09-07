from pathlib import Path
import shutil
import copy
import traceback
import datetime
import tempfile
import os
import logging
logger = logging.getLogger(__name__)


class TransformationProject:
    def __init__(self, transforms, picker, c_filename, c_code, avoid=None):
        self.transforms = copy.deepcopy(transforms)
        self.picker = picker

        self.original_c_filename = self.c_filename = c_filename
        self.c_code = c_code

        self.avoid = avoid

    def __enter__(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

        tmp_c_filename = self.tmp_dir / self.c_filename
        if self.c_code is None:
            shutil.copy(self.c_filename, tmp_c_filename)
        else:
            with open(tmp_c_filename, 'w') as f:
                f.write(self.c_code)
        self.c_filename = tmp_c_filename

        return self

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.tmp_dir)

    def log(self, *args):
        logger.info('[%s] %s', self.original_c_filename, ' '.join(str(a) for a in args))

    def log_error(self, *args):
        logger.error('[%s] %s', self.original_c_filename, ' '.join(str(a) for a in args))

    def apply_all(self, return_applied=False):
        """Do C source-to-source translation"""

        transformations_applied = []

        # Apply all transforms one at a time
        new_lines = None
        while len(self.transforms) > 0:
            if len(self.transforms) == 0:
                self.log('Quitting early, ran out of transforms')
                break
            t = self.transforms[0]
            try:
                new_lines = t(self.c_filename, picker=self.picker, avoid_lines=self.avoid).run()

                # If it could not be applied, skip this transformation.
                # Most commonly means the transformation had no slot.
                if new_lines == None:
                    self.log(f'Could not apply {t.__name__}.')
                    self.transforms.remove(t)
                    continue

                # Successfully applied the transformation.
                with open(self.c_filename, 'w') as f:
                    f.writelines(new_lines)
                self.transforms.remove(t)
                transformations_applied.append(t)
                self.log('Applied', t.__name__)
            except Exception as e:
                self.log(f'Error applying {t.__name__}: {e}. Stack trace written to errors.log.')
                self.log_error(self.c_filename, t.__name__, e, '\n', traceback.format_exc())
                self.transforms.remove(t)
        if return_applied:
            return new_lines, transformations_applied
        else:
            return new_lines
