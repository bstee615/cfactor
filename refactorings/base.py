from pathlib import Path
import srcml
import refactorings
from refactorings.joern import JoernInfo


class BaseTransformation:
    def __init__(self, c_file, **kwargs):
        self.c_file = Path(c_file)
        with open(self.c_file) as f:
            self.old_lines = f.readlines()
        # If file has CRLF line endings, then it will screw with Python's counting the file offsets.
        with open(self.c_file, newline='\r\n') as f:
            self.old_text = f.read()
        if '\r' in self.old_text:
            raise Exception(f'{c_file} is CRLF')
        
        if "picker" in kwargs:
            self.picker = kwargs.get("picker")
        else:
            self.picker = refactorings.first_picker

        self.info = {}
        if "project" in kwargs:
            self.info["project"] = Path(kwargs.get("project"))
        else:
            self.info["project"] = self.c_file.parent

        if "exclude" in kwargs:
            self.info["exclude"] = kwargs.get("exclude")
        else:
            self.info["exclude"] = None

        self.joern = JoernInfo(self.c_file, self.info["project"], self.info["exclude"])
        self.srcml_root = srcml.get_xml_from_file(self.c_file)

    def run(self):
        all_targets = self.get_targets()
        if len(all_targets) == 0:
            return None
        target = self.picker(all_targets)
        return self.apply(target)
