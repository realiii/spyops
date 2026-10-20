# -*- coding: utf-8 -*-
"""
Planarize Geometries
"""


from typing import TYPE_CHECKING, Union

from shapely.set_operations import union_all

from spyops.geometry.compare import remove_repeats
from spyops.shared.hint import GRID_SIZE


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry


def planarize(geoms: Union[list, 'ndarray'], *, grid_size: GRID_SIZE = None) \
        -> Union['BaseGeometry', 'BaseMultipartGeometry']:
    """
    Planarize geometries
    """
    geoms = remove_repeats(geoms, grid_size=grid_size)
    return union_all(geoms, grid_size=grid_size)
# End planarize function


if __name__ == '__main__':  # pragma: no cover
    pass
