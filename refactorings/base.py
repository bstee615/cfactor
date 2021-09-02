import shutil
from pathlib import Path
from refactorings.bad_node_exception import BadNodeException
import refactorings
from refactorings.joern import JoernInfo
import srcml
import difflib
import copy
import random
import traceback
import logging

logger = logging.getLogger(__name__)


# https://stackoverflow.com/a/30007726
class PrefixedLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, prefix, logger):
        super(PrefixedLoggerAdapter, self).__init__(logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        return '[%s] %s' % (self.prefix, msg), kwargs


class BaseTransformation:
    logger = logging.getLogger('BaseTransformation')

    def __init__(self, c_file, **kwargs):
        # Load target source file
        self.c_file = Path(c_file)
        project = Path(kwargs.get("project", self.c_file.parent))
        prefix = f'{project}:{self.c_file}'
        self.logger = PrefixedLoggerAdapter(prefix, self.logger)

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

        try:
            exclude_files = kwargs.get("exclude", None)
            self.joern = JoernInfo(self.c_file, project, exclude_files)
        except Exception as e:
            self.joern = None
            self.logger.exception(e)

        try:
            self.srcml_root = srcml.get_xml_from_file(self.c_file)
        except Exception as e:
            self.srcml_root = None
            self.logger.exception(e)

    def apply_wrapper(self, target):
        try:
            return self.apply(target)
        except (NotImplementedError, AssertionError) as e:
            raise BadNodeException(*e.args)

    def run(self):
        all_targets = self.get_targets()
        new_lines = None
        while len(all_targets) > 0:
            target = self.picker(all_targets, rng=self.rng)
            old_srcml_root, old_joern = copy.deepcopy(self.srcml_root), copy.deepcopy(self.joern)
            try:
                new_lines = self.apply_wrapper(target)
            except BadNodeException:
                new_lines = None
                all_targets.remove(target)
                self.srcml_root = old_srcml_root
                self.joern = old_joern
                self.logger.exception(f'target={self.joern.node_type[target]}@{self.joern.node_location[target]}')
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
