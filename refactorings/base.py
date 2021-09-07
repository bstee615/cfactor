import abc
import logging
import random
from abc import ABC

from refactorings.bad_node_exception import BadNodeException
from refactorings.defaults import first_picker
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
        while len(all_targets) > 0:
            target = self.picker(all_targets, rng=self.rng)
            try:
                new_lines = self.run_target(target)
            except BadNodeException as e:
                all_targets.remove(target)
                continue
            if new_lines is None:
                return None
            elif self.avoid_lineno is None or len(self.avoid_lineno) == 0:
                return new_lines
            else:
                raise NotImplementedError('avoid lines is not supported')
        return


class SrcMLTransformation(BaseTransformation, ABC):
    def __init__(self, c_file, c_code, *args, **kwargs):
        super().__init__(c_file, c_code, *args, **kwargs)
        self.srcml = SrcMLInfo(c_code)
