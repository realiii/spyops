# -*- coding: utf-8 -*-
"""
Utility Functions
"""


from typing import Any, TYPE_CHECKING, Union

from numpy import diff, ndarray, nonzero
from shapely import force_2d, force_3d
from shapely.io import from_wkb

from spyops.geometry.enumeration import DimensionOption
from spyops.shared.constant import GEOMS_ATTR


if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry.base import (
        BaseMultipartGeometry, BaseGeometry, GeometrySequence)


def nada(value: Any) -> Any:
    """
    Nada
    """
    return value
# End nada function


def get_geoms(geom: 'BaseMultipartGeometry') -> 'GeometrySequence':
    """
    Get Geometries
    """
    return getattr(geom, GEOMS_ATTR)
# End get_geoms function


def get_geoms_iter(geom: Union['BaseGeometry', 'BaseMultipartGeometry']) \
        -> Union['GeometrySequence', list['BaseGeometry']]:
    """
    Get Geometries for Iteration
    """
    return getattr(geom, GEOMS_ATTR, [geom])
# End get_geoms_iter function


def filter_features(features: list[tuple]) -> list[tuple]:
    """
    Filter Features, removing empty
    """
    return [feature for feature in features if not feature[0].is_empty]
# End filter_features function


def find_slice_indexes(indexes: 'ndarray') -> tuple[int, ...]:
    """
    Find Slice Indexes, include the final index to allow for easier striding
    """
    if not len(indexes):
        return ()
    ids, = nonzero(diff(indexes))
    ids += 1
    return 0, *[int(i) for i in ids], len(indexes)
# End find_slice_indexes function


def to_shapely(features: list[tuple], option: DimensionOption = DimensionOption.SAME) -> Union[list, 'ndarray']:
    """
    To Shapely Geometry from Fudgeo
    """
    geometries = [from_wkb(g.wkb) for g, *_ in features]
    if option == DimensionOption.TWO_D:
        # noinspection PyTypeChecker
        return force_2d(geometries)
    elif option == DimensionOption.THREE_D:
        # noinspection PyTypeChecker
        return force_3d(geometries)
    return geometries
# End to_shapely function


if __name__ == '__main__':  # pragma: no cover
    pass
