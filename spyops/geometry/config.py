# -*- coding: utf-8 -*-
"""
Geometry Configuration
"""


from collections import defaultdict
from functools import partial
from math import nan
from typing import Any, Callable, NamedTuple, TYPE_CHECKING, Type, Union

from bottleneck import nanmean
from fudgeo.geometry import LineStringM, LineStringZM
from fudgeo.enumeration import ShapeType
from shapely import LineString, MultiLineString
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb
from shapely.linear import line_merge

from spyops.geometry.convert import GEOMETRY_CAST
from spyops.geometry.lookup import (
    FUDGEO_GEOMETRY_LOOKUP, SHAPELY_GEOMETRY_LOOKUP)
from spyops.geometry.util import get_geoms, nada
from spyops.geometry.wa import USE_WORKAROUNDS
from spyops.shared.constant import SRS_ID_WKB
from spyops.shared.keywords import GEOMS_ATTR, HAS_M_KEY, HAS_Z_KEY, SRS_ID_KEY

if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry


class GeometryConfig(NamedTuple):
    """
    Geometry Configuration
    """
    geometry_cls: Any
    is_multi: bool
    filter_types: tuple[Type['BaseGeometry'], Type['BaseMultipartGeometry']]
    srs_id: int
    combiner: Callable
    caster: Callable | None
# End GeometryConfig class


def geometry_config(target: 'FeatureClass', cast_geom: bool) -> GeometryConfig:
    """
    Geometry Configuration
    """
    has_m = target.has_m
    has_z = target.has_z
    shape_type = target.shape_type
    cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][has_z, has_m]
    filter_types = SHAPELY_GEOMETRY_LOOKUP[shape_type]
    combiner = _get_combiner(shape_type, has_m=has_m)
    srs_id = target.spatial_reference_system.srs_id
    if cast_geom:
        caster = GEOMETRY_CAST[target.shape_type]
        kwargs = {SRS_ID_KEY: srs_id, HAS_Z_KEY: has_z, HAS_M_KEY: has_m}
        caster = partial(caster, **kwargs)
    else:
        caster = None
    return GeometryConfig(
        geometry_cls=cls, is_multi=target.is_multi_part,
        filter_types=filter_types, combiner=combiner,
        srs_id=srs_id, caster=caster)
# End geometry_config function


def _combine_lines(geom: Union[LineString, MultiLineString]) \
        -> Union[LineString, MultiLineString]:
    """
    Combine Lines using Directed Line Merge
    """
    if hasattr(geom, GEOMS_ATTR):
        # noinspection PyTypeChecker
        return line_merge(geom, directed=True)
    return geom
# End _combine_lines function


def _combine_lines_workaround(geom: Union[LineString, MultiLineString]) \
        -> Union[LineString, MultiLineString]:
    """
    Combine Lines using Directed Line Merge, this will only be applied when a
    workaround is needed and there are measures on the incoming geometry.
    """
    if not hasattr(geom, GEOMS_ATTR) or geom.is_empty:
        return geom
    result = line_merge(geom, directed=True)
    if result.is_empty:
        return geom
    measures = defaultdict(list)
    if has_z := geom.has_z:
        cls = LineStringZM
    else:
        cls = LineStringM
    for *key, m in get_coordinates(geom, include_z=has_z, include_m=True):
        measures[tuple(key)].append(m)
    if isinstance(result, LineString):
        # noinspection PyTypeChecker
        return from_wkb(_make_measured_line(
            result, has_z=has_z, cls=cls, measures=measures))
    else:
        wkb = [_make_measured_line(
            line, has_z=has_z, cls=cls, measures=measures)
            for line in get_geoms(result)]
        return MultiLineString(from_wkb(wkb).tolist())
# End _combine_lines_workaround function


def _make_measured_line(geom: LineString, has_z: bool,
                        cls: Type[LineStringZM | LineStringM],
                        measures: defaultdict[
                            tuple[float, ...], list[float]]) -> bytes:
    """
    Make a Measured Line from a Shapely LineString, looking up measures
    based on the coordinates.
    """
    coords = []
    coordinates = get_coordinates(geom, include_z=has_z)
    for key in coordinates:
        m = nanmean(measures.get(tuple(key), [nan]))
        coords.append((*key, m))
    return cls(coords, srs_id=SRS_ID_WKB).wkb
# End _make_measured_line function


def _get_combiner(shape_type: str, has_m: bool) -> Callable:
    """
    Get Combiner Function
    """
    if ShapeType.linestring in shape_type:
        if has_m and USE_WORKAROUNDS.line_merge:
            return _combine_lines_workaround
        else:
            return _combine_lines
    return nada
# End _get_combiner function


if __name__ == '__main__':  # pragma: no cover
    pass
