import abc
import shutil
from pathlib import Path
from refactorings.bad_node_exception import BadNodeException
import refactorings
from refactorings.joern import JoernInfo
import difflib
import copy
import random
import traceback
import logging

from srcml import SrcMLInfo

logger = logging.getLogger(__name__)


# https://stackoverflow.com/a/30007726
class PrefixedLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, prefix, logger):
        super(PrefixedLoggerAdapter, self).__init__(logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        return '[%s] %s' % (self.prefix, msg), kwargs


class BaseTransformation(abc.ABC):
    logger = logging.getLogger('BaseTransformation')

    def __init__(self, c_file, **kwargs):
        # Load target source file
        self.c_file = Path(c_file)

        with open(self.c_file) as f:
            self.old_lines = f.readlines()
        # If file has CRLF line endings, then it will screw with Python's counting the file offsets.
        with open(self.c_file, newline='\r\n') as f:
            self.old_text = f.read()
        if '\r' in self.old_text:
            raise Exception(f'CRLF')
            
        self.rng = random.Random(0)
        
        self.picker = kwargs.get("picker", refactorings.first_picker)
        if "avoid_lines" in kwargs:
            self.avoid_lineno = kwargs.get("avoid_lines")
        else:
            self.avoid_lineno = set()

    @abc.abstractmethod
    def get_targets(self, target):
        """
        Get targets to be consumed by get_targets.
        All targets should have a useful equality function (i.e. works well with list.remove()).
        """
        pass

    @abc.abstractmethod
    def _apply(self, target):
        """
        Apply the transformation to self.c_file and return new lines for the file.
        Throw all exceptions up to be caught by run_target().
        """
        pass

    def run_target(self, target):
        try:
            return self._apply(target)
        except (NotImplementedError, AssertionError) as e:
            self.handle_exception(e)
            raise BadNodeException(*e.args)

    @classmethod
    def get_indent(cls, line):
        return line[:-len(line.lstrip())]

    def run(self):
        all_targets = self.get_targets()
        new_lines = None
        while len(all_targets) > 0:
            target = self.picker(all_targets, rng=self.rng)
            try:
                new_lines = self.run_target(target)
            except BadNodeException as e:
                new_lines = None
                all_targets.remove(target)
                self.logger.info(f'Bad node target={self.joern.node_type[target]} at {self.c_file}{self.joern.node_location[target]}: {e}')
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
                    continue
                else:
                    return new_lines
        return


class JoernTransformation(BaseTransformation):
    def __init__(self, c_file, *args, **kwargs):
        super().__init__(c_file, *args, **kwargs)
        self.joern = JoernInfo(c_file)


class SrcMLTransformation(BaseTransformation):
    def __init__(self, c_file, *args, **kwargs):
        super().__init__(c_file, *args, **kwargs)
        self.srcml = SrcMLInfo(self.old_text)
