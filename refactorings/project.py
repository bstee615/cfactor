from pathlib import Path
import shutil
import copy
import traceback
import datetime
import tempfile


class TransformationProject:
    def __init__(self, transforms, picker, project, c_filename, exclude, keep_tmp):
        self.transforms = copy.deepcopy(transforms)
        self.picker = picker
        self.info = {"exclude": exclude}

        self.project, self.c_filename = project, c_filename

        self.keep_tmp = keep_tmp
                
    def __enter__(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

        tmp_project = self.tmp_dir / self.project.name
        shutil.copytree(self.project, tmp_project)

        tmp_c_filename = tmp_project / self.c_filename.relative_to(self.project)
        shutil.copy(self.c_filename, tmp_c_filename)

        self.project = tmp_project
        self.c_filename = tmp_c_filename
        self.info["project"] = self.c_filename.parent
        
        self.transform_filename = self.c_filename.parent / (self.c_filename.stem + '.transforms.txt')
        if self.transform_filename.exists():
            self.transform_filename.unlink()
        
        self.transformations_applied = []
        
        return self

    def __exit__(self, type, value, traceback):
        if not self.keep_tmp:
            shutil.rmtree(self.tmp_dir)

    def log_transforms_applied(self, t):
        """Log after each transform, for debugging in case the procedure is errored."""
        with open(self.transform_filename, 'a') as f:
            f.write(f'{t.__name__}\n')

    def log(self, *args):
        print(*args)

    def log_error(self, *args):
        with open('errors.log', 'a') as f:
            print(*args, file=f)

    def apply(self, t):
        try:
            new_lines = t(self.c_filename, picker=self.picker, info=self.info).run()

            # If it could not be applied, skip this transformation.
            # Most commonly means the transformation had no slot.
            if new_lines == None:
                self.log(f'Could not apply {t.__name__}.')
                self.transforms.remove(t)
                return

            # Successfully applied the transformation.
            self.log_transforms_applied(t)
            with open(self.c_filename, 'w') as f:
                f.writelines(new_lines)
            shutil.copy2(self.c_filename, self.tmp_dir / (f'{self.c_filename.name}.{len(self.transformations_applied)}.{t.__name__}'))
            self.transforms.remove(t)
            self.transformations_applied.append(t)
            self.log('Applied', t.__name__)
        except Exception as e:
            self.log(f'Error applying {t.__name__}: {e}. Stack trace written to errors.log.')
            self.log_error(f'***Exception {self.project} {self.project} {t.__name__} ({datetime.datetime.now()})***', e)
            self.log_error(traceback.format_exc())
            self.transforms.remove(t)

    def apply_all(self, return_applied=False):
        """Do C source-to-source translation"""

        self.transformations_applied = []

        # Apply all transforms one at a time
        shutil.copy2(self.c_filename, self.tmp_dir / (self.c_filename.name + '.back'))
        while len(self.transforms) > 0:
            if len(self.transforms) == 0:
                self.log('Quitting early, ran out of transforms')
                break
            t = self.transforms[0]
            self.apply(t)
        if return_applied:
            return Path(self.c_filename), self.transformations_applied
        else:
            return Path(self.c_filename)


class TransformationsFactory:
    def __init__(self, transforms, picker):
        self.transforms = copy.deepcopy(list(transforms))
        self.picker = picker

    def make_project(self, c_filename, project=None, exclude=None, keep_tmp=False):
        if project is None:
            project = c_filename.parent
        return TransformationProject(self.transforms, self.picker, project, c_filename, exclude, keep_tmp=keep_tmp)
