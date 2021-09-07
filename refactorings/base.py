import abc
import shutil
from pathlib import Path
from refactorings.bad_node_exception import BadNodeException
from refactorings.joern import JoernInfo
from refactorings.defaults import first_picker
import difflib
import copy
import random
import traceback
import logging

from srcml import SrcMLInfo

logger = logging.getLogger(__name__)


class BaseTransformation(abc.ABC):
    logger = logging.getLogger('BaseTransformation')

    def __init__(self, c_file, c_code, picker=first_picker, avoid_lines=None):
        # Load target source file
        if '\r' in c_code:
            raise Exception(f'CRLF')
            
        self.rng = random.Random(0)

        self.picker = picker
        if avoid_lines is None:
            avoid_lines = set()
        self.avoid_lineno = avoid_lines

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

    def run_target(self, target):
        try:
            super().run_target(target)
        except BadNodeException as e:
            self.logger.exception(
                f'Bad node target={self.joern.node_type[target]} at {self.c_file}{self.joern.node_location[target]}',
                exc_info=e
            )
            raise e


class SrcMLTransformation(BaseTransformation):
    def __init__(self, c_file, c_code, *args, **kwargs):
        super().__init__(c_file, c_code, *args, **kwargs)
        self.srcml = SrcMLInfo(c_code)
