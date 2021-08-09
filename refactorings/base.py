from pathlib import Path
import srcml
import refactorings
from refactorings.joern import JoernInfo


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

        try:
            project = Path(kwargs.get("project", self.c_file.parent))
            exclude_files = kwargs.get("exclude", None)
            tmp_dir = Path(kwargs.get("tmp_dir", '/tmp'))
            self.joern = JoernInfo(self.c_file, project, exclude_files, tmp_dir)
        except:
            self.joern = None
        try:
            self.srcml_root = srcml.get_xml_from_file(self.c_file)
        except:
            self.srcml_root = None

    def run(self):
        all_targets = self.get_targets()
        if len(all_targets) == 0:
            return None
        target = self.picker(all_targets)
        return self.apply(target)
