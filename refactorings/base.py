from pathlib import Path
from refactorings.bad_node_exception import BadNodeException
import srcml
import refactorings
from refactorings.joern import JoernInfo
import difflib
import copy
import random
import traceback


class BaseTransformation:
    def __init__(self, c_file, **kwargs):
        # Load target source file
        self.c_file = Path(c_file)
        with open(self.c_file) as f:
            self.old_lines = f.readlines()
        # If file has CRLF line endings, then it will screw with Python's counting the file offsets.
        with open(self.c_file, newline='\r\n') as f:
            self.old_text = f.read()
        if '\r' in self.old_text:
            raise Exception(f'{c_file} is CRLF')
            
        self.rng = random.Random(0)
        
        self.picker = kwargs.get("picker", refactorings.first_picker)
        if "avoid_lines" in kwargs:
            self.avoid_lineno = kwargs.get("avoid_lines")
        else:
            self.avoid_lineno = set()

        project = Path(kwargs.get("project", self.c_file.parent))
        try:
            exclude_files = kwargs.get("exclude", None)
            tmp_dir = Path(kwargs.get("tmp_dir", '/tmp'))
            self.joern = JoernInfo(self.c_file, project, exclude_files, tmp_dir)
        except Exception as e:
            self.joern = None
            with open('errors.log', 'a') as f:
                f.write(f'Error loading Joern for {project} {self.c_file}: {e}\n{traceback.format_exc()}\n')

        try:
            self.srcml_root = srcml.get_xml_from_file(self.c_file)
        except Exception as e:
            self.srcml_root = None
            with open('errors.log', 'a') as f:
                f.write(f'Error loading srcML for {project} {self.c_file}: {e}\n{traceback.format_exc()}\n')

    def run(self):
        all_targets = self.get_targets()
        new_lines = None
        while len(all_targets) > 0:
            target = self.picker(all_targets, rng=self.rng)
            old_srcml_root, old_joern = copy.deepcopy(self.srcml_root), copy.deepcopy(self.joern)
            try:
                new_lines = self.apply(target)
            except BadNodeException as e:
                new_lines = None
                all_targets.remove(target)
                self.srcml_root = old_srcml_root
                self.joern = old_joern
                with open('errors.log', 'a') as f:
                    print(f'BadNodeException({self.c_file}): {e}', file=f)
                continue
            if new_lines is None:
                return None
            elif self.avoid_lineno is None or len(self.avoid_lineno) == 0:
                return new_lines
            else:
                # Check if the off-limits lines are changed.
                # Ignore whitespace on the left and right.
                # TODO: Also ignore intra-line whitespace?
                diff = list(difflib.ndiff([l.strip() + '\n' for l in self.old_lines], [l.strip() + '\n' for l in new_lines]))
                changed_or_same = [d for d in diff if d[:2] in ('  ', '- ')]
                changed_lines_idx = {i for i, l in enumerate(changed_or_same) if l[:2] == '- '}
                changed_linenos = {i+1 for i in changed_lines_idx}
                if changed_linenos.intersection(self.avoid_lineno):
                    new_lines = None
                    all_targets.remove(target)
                    self.srcml_root = old_srcml_root
                    self.joern = old_joern
                    continue
                else:
                    return new_lines
        return new_lines
