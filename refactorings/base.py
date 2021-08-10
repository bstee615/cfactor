from pathlib import Path
from refactorings.bad_node_exception import BadNodeException
import srcml
import refactorings
from refactorings.joern import JoernInfo
import difflib
import copy


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
        
        self.picker = kwargs.get("picker", refactorings.first_picker)
        self.avoid_lineno = set(kwargs.get("avoid_lines", set()))

        try:
            project = Path(kwargs.get("project", self.c_file.parent))
            exclude_files = kwargs.get("exclude", None)
            tmp_dir = Path(kwargs.get("tmp_dir", '/tmp'))
            self.joern = JoernInfo(self.c_file, project, exclude_files, tmp_dir)
        except Exception:
            self.joern = None
        try:
            self.srcml_root = srcml.get_xml_from_file(self.c_file)
        except Exception:
            self.srcml_root = None

    def run(self):
        all_targets = self.get_targets()
        new_lines = None
        while len(all_targets) > 0:
            target = self.picker(all_targets)
            old_srcml_root, old_joern = copy.deepcopy(self.srcml_root), copy.deepcopy(self.joern)
            try:
                new_lines = self.apply(target)
            except BadNodeException as e:
                new_lines = None
                all_targets.remove(target)
                self.srcml_root = old_srcml_root
                self.joern = old_joern
                with open('errors.log', 'a') as f:
                    print(f'BadNodeException: {e}', file=f)
                continue
            if new_lines is None:
                return None
            elif len(self.avoid_lineno) == 0:
                return new_lines
            else:
                # Check if the off-limits lines are changed
                diff = list(difflib.ndiff(self.old_lines, new_lines))
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
