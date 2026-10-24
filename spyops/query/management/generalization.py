# -*- coding: utf-8 -*-
"""
Query Classes for management.generalization module
"""


from functools import partial
from typing import Callable

from spyops.geometry.multi import build_dissolved
from spyops.query.management.shared import AbstractQueryDissolveStatistics


class QueryDissolve(AbstractQueryDissolveStatistics):
    """
    Queries for Dissolve
    """
    def _get_builder(self, shape_type: str) -> Callable:
        """
        Get Builder based on Shape Type
        """
        return partial(
            build_dissolved, shape_type=shape_type, grid_size=self.grid_size)
    # End _get_builder method
# End QueryDissolve class


if __name__ == '__main__':  # pragma: no cover
    pass
