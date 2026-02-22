# -*- coding: utf-8 -*-
"""
Utility Functions
"""


from typing import Any, Callable, TYPE_CHECKING, Union

from numpy import array, diff, ndarray, nonzero, ones
from shapely import force_2d, force_3d, get_num_interior_rings
from shapely.constructive import point_on_surface
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


def to_shapely(features: list[tuple], transformer: Callable | None,
               option: DimensionOption = DimensionOption.SAME) \
        -> tuple[list[tuple], 'ndarray']:
    """
    Convert to Shapely Geometry from Fudgeo Geometry, optionally changing
    geometry dimension by forcing to 2D or 3D and/or transforming.

    When a transformer is provided the geometries are transformed, validity
    checked, and valid geometries (and corresponding features) are returned.
    """
    geometries = from_wkb([g.wkb for g, *_ in features])
    if transformer:
        geometries = transformer(geometries)
        validity = get_validity(geometries, transformer)
        features = [feature for feature, v in zip(features, validity) if v]
    if option == DimensionOption.TWO_D:
        geometries = force_2d(geometries)
    elif option == DimensionOption.THREE_D:
        geometries = force_3d(geometries)
    return features, geometries
# End to_shapely function


def get_validity(geoms: 'ndarray', transformer: Callable | None) -> 'ndarray':
    """
    Get Validity, True if geometry is valid and not empty and not None
    """
    if transformer is None:
        return ones(len(geoms), dtype=bool)
    return array([not (g is None or g.is_empty or not g.is_valid)
                  for g in geoms], dtype=bool)
# End get_validity function


def get_hole_count(geoms: 'ndarray') -> list[int]:
    """
    Get Hole Count for Polygons or MultiPolygons
    """
    return [sum(get_num_interior_rings(get_geoms_iter(g))) for g in geoms]
# End get_hole_count function


def get_inside_xy(geoms: 'ndarray') -> list[tuple[float, float]]:
    """
    Get Inside XY
    """
    return [(pt.x, pt.y) for pt in point_on_surface(geoms)]
# End get_inside_xy function


if __name__ == '__main__':  # pragma: no cover
    pass
