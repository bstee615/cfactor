from abc import ABC

from refactorings.bad_node_exception import BadNodeException
from refactorings.base import BaseTransformation
from refactorings.joern import JoernInfo


class JoernTransformation(BaseTransformation, ABC):
    def __init__(self, c_file, *args, **kwargs):
        super().__init__(c_file, *args, **kwargs)
        self.joern = JoernInfo(c_file)
        # raise NotImplementedError('Joern is not supported for now')

    def run_target(self, target):
        try:
            super().run_target(target)
        except BadNodeException as e:
            self.logger.exception(
                f'Bad node target={self.joern.node_type[target]} at {self.c_file}{self.joern.node_location[target]}',
                exc_info=e
            )
            raise e