# -*- coding: utf-8 -*-
"""
Geometry Functionality
"""


from math import nan
from typing import Any, Callable, Type

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import GeometryType
from fudgeo.geometry import (
    LineString, LineStringM, LineStringZ, LineStringZM, MultiLineString,
    MultiLineStringM, MultiLineStringZ, MultiLineStringZM, MultiPoint,
    MultiPointM, MultiPointZ, MultiPointZM, MultiPolygon, MultiPolygonM,
    MultiPolygonZ, MultiPolygonZM, Point, PointM, PointZ, PointZM, Polygon,
    PolygonM, PolygonZ, PolygonZM)
from fudgeo.util import get_extent
from numpy import isfinite
from shapely import (
    LineString as ShapelyLineString, MultiLineString as ShapelyMultiLineString,
    MultiPoint as ShapelyMultiPoint, MultiPolygon as ShapelyMultiPolygon,
    Point as ShapelyPoint, Polygon as ShapelyPolygon)
from shapely.constructive import boundary, make_valid
from shapely.creation import prepare
from shapely.geometry.base import (
    BaseGeometry as ShapelyGeometry,
    BaseMultipartGeometry as ShapelyMultipartGeometry)
from shapely.io import from_wkb
from shapely.linear import line_merge
from shapely.ops import unary_union

from geomio.shared.base import GeometryConfig
from geomio.shared.constant import (
    GEOMS_ATTR, LINES_ATTR, POINTS_ATTR, POLYGONS_ATTR)
from geomio.shared.enumeration import OutputTypeOption
from geomio.shared.exception import OperationsError
from geomio.shared.field import get_geometry_column_name
from geomio.shared.hint import EXTENT

SHAPELY_GEOMETRY_LOOKUP: dict[str, tuple[Any, Any]] = {
    GeometryType.point: (ShapelyPoint, ShapelyMultiPoint),
    GeometryType.multi_point: (ShapelyPoint, ShapelyMultiPoint),
    GeometryType.linestring: (ShapelyLineString, ShapelyMultiLineString),
    GeometryType.multi_linestring: (ShapelyLineString, ShapelyMultiLineString),
    GeometryType.polygon: (ShapelyPolygon, ShapelyMultiPolygon),
    GeometryType.multi_polygon: (ShapelyPolygon, ShapelyMultiPolygon),
}


FUDGEO_GEOMETRY_LOOKUP: dict[str, dict[tuple[bool, bool], Any]] = {
    GeometryType.point: {
        (False, False): Point,
        (True, False): PointZ,
        (False, True): PointM,
        (True, True): PointZM},
    GeometryType.multi_point: {
        (False, False): MultiPoint,
        (True, False): MultiPointZ,
        (False, True): MultiPointM,
        (True, True): MultiPointZM},
    GeometryType.linestring: {
        (False, False): LineString,
        (True, False): LineStringZ,
        (False, True): LineStringM,
        (True, True): LineStringZM},
    GeometryType.multi_linestring: {
        (False, False): MultiLineString,
        (True, False): MultiLineStringZ,
        (False, True): MultiLineStringM,
        (True, True): MultiLineStringZM},
    GeometryType.polygon: {
        (False, False): Polygon,
        (True, False): PolygonZ,
        (False, True): PolygonM,
        (True, True): PolygonZM},
    GeometryType.multi_polygon: {
        (False, False): MultiPolygon,
        (True, False): MultiPolygonZ,
        (False, True): MultiPolygonM,
        (True, True): MultiPolygonZM}
}


def build_multi(feature_class: FeatureClass | None) \
        -> ShapelyMultiPoint | ShapelyMultiLineString | ShapelyMultiPolygon | None:
    """
    Build Multi Point, Multi Line or Multi Polygon
    """
    if not feature_class:
        return None
    shape_type = feature_class.shape_type
    if shape_type in (GeometryType.point, GeometryType.multi_point):
        return _build_multi_point(feature_class)
    elif shape_type in (GeometryType.linestring, GeometryType.multi_linestring):
        return _build_multi_linestring(feature_class)
    elif shape_type in (GeometryType.polygon, GeometryType.multi_polygon):
        return _build_multi_polygon(feature_class)
    else:
        raise ValueError(f'Unsupported shape type: {shape_type}')
# End build_multi function


def _get_geoms(feature_class: FeatureClass, attr: str,
               checker: Callable[[ShapelyGeometry], ShapelyGeometry | None]) \
        -> list[ShapelyPoint] | list[ShapelyLineString] | list[ShapelyPolygon]:
    """
    Get Shapely Geometries from Feature Class
    """
    geoms = []
    column_name = get_geometry_column_name(
        feature_class, include_geom_type=True)
    with feature_class.geopackage.connection as cin:
        cursor = cin.execute(
            f"""SELECT {column_name} 
                FROM {feature_class.escaped_name}""")
        while geometries := cursor.fetchmany(FETCH_SIZE):
            for geometry, in geometries:
                for geom in getattr(geometry, attr, [geometry]):
                    g = from_wkb(geom.wkb)
                    if checker(g) is None:
                        continue
                    geoms.append(g)
    return geoms
# End _get_geoms function


def _build_multi_polygon(feature_class: FeatureClass) -> ShapelyMultiPolygon:
    """
    Build MultiPolygon from Polygon or MultiPolygon Feature Class
    """
    # noinspection PyTypeChecker
    geoms = _get_geoms(feature_class, attr=POLYGONS_ATTR, checker=check_polygon)
    if not geoms:
        return ShapelyMultiPolygon()
    multi = unary_union(geoms)
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _build_multi_polygon function


def _build_multi_linestring(feature_class: FeatureClass) -> ShapelyMultiLineString:
    """
    Build MultiLineString from LineString or MultiLineString Feature Class
    """
    # noinspection PyTypeChecker
    geoms = _get_geoms(feature_class, attr=LINES_ATTR, checker=check_linestring)
    multi = ShapelyMultiLineString(geoms)
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _build_multi_linestring function


def _build_multi_point(feature_class: FeatureClass) -> ShapelyMultiPoint:
    """
    Build MultiPoint from Point or MultiPoint Feature Class
    """
    # noinspection PyTypeChecker
    geoms = _get_geoms(feature_class, attr=POINTS_ATTR, checker=check_point)
    multi = ShapelyMultiPoint(geoms)
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _build_multi_point function


def check_polygon(polygon: ShapelyPolygon | ShapelyMultiPolygon) \
        -> ShapelyMultiPolygon | ShapelyPolygon | None:
    """
    Check Polygon
    """
    return _check_geometry(
        polygon, method_name='structure', cls=ShapelyPolygon,
        multi_cls=ShapelyMultiPolygon)
# End check_polygon function


def check_linestring(geom: ShapelyLineString | ShapelyMultiLineString) \
        -> ShapelyLineString | ShapelyMultiLineString | None:
    """
    Check LineString
    """
    return _check_geometry(
        geom, method_name='linework', cls=ShapelyLineString,
        multi_cls=ShapelyMultiLineString)
# End check_linestring function


def check_point(geom: ShapelyPoint | ShapelyMultiPoint) \
        -> ShapelyPoint | ShapelyMultiPoint | None:
    """
    Check Point
    """
    if geom.is_empty:
        return None
    return geom
# End check_point function


def _check_geometry(geom: ShapelyGeometry, method_name: str,
                    cls: Type[ShapelyGeometry],
                    multi_cls: Type[ShapelyMultipartGeometry]) \
        -> ShapelyGeometry | ShapelyMultipartGeometry | None:
    """
    Check Geometry (for LineString and Polygon)
    """
    if geom.is_valid:
        return geom
    # noinspection PyTypeChecker
    geom = make_valid(geom, method=method_name)
    if not geom.is_valid:
        return None
    geoms = [p for p in getattr(geom, GEOMS_ATTR, [geom])
             if p.is_valid and isinstance(p, cls)]
    if not geoms:
        return None
    if len(geoms) == 1:
        return geoms[0]
    # noinspection PyArgumentList
    return multi_cls(geoms)
# End _check_geometry function


def _nada(value: Any) -> Any:
    """
    Nada
    """
    return value
# End _nada function


def _as_lines(geoms: list[ShapelyPolygon] | list[ShapelyMultiPolygon]) \
        -> list[ShapelyLineString | ShapelyMultiLineString]:
    """
    Convert Polygons to LineStrings
    """
    # noinspection PyTypeChecker
    return boundary(geoms)
# End _as_lines function


def _combine_lines(value: ShapelyLineString | ShapelyMultiLineString) \
        -> ShapelyLineString | ShapelyMultiLineString:
    """
    Combine Lines using Directed Line Merge
    """
    if isinstance(value, ShapelyMultiLineString):
        return line_merge(value, directed=True)
    return value
# End _combine_lines function


def _use_boundary_factory(source_shape_type: str, operator_shape_type: str,
                          output_type_option: OutputTypeOption) \
        -> tuple[bool, bool]:
    """
    Factory function to determine if boundary should be used during overlay
    operation.  Based on output type option and shape types of source and
    operator feature classes.
    """
    points = GeometryType.point, GeometryType.multi_point
    polygons = GeometryType.polygon, GeometryType.multi_polygon
    lines = GeometryType.linestring, GeometryType.multi_linestring
    if (output_type_option == OutputTypeOption.SAME or
            source_shape_type in points):
        return False, False
    if source_shape_type in polygons and operator_shape_type in polygons:
        return True, True
    if output_type_option == OutputTypeOption.POINT:
        if source_shape_type in lines and operator_shape_type in polygons:
            return False, True
    return False, False
# End _use_boundary_factory function


def get_geometry_converters(source: FeatureClass, operator: FeatureClass,
                            output_type_option: OutputTypeOption) \
        -> tuple[Callable, Callable]:
    """
    Get Geometry Converters based on Source and Operator Shape Types and
    the requested output type option.
    """
    convert_src, convert_op = _use_boundary_factory(
        source.shape_type, operator_shape_type=operator.shape_type,
        output_type_option=output_type_option)
    src_converter = op_converter = _nada
    if convert_src:
        src_converter = _as_lines
    if convert_op:
        op_converter = _as_lines
    return src_converter, op_converter
# End get_geometry_converters function


def geometry_config(target: FeatureClass) -> GeometryConfig:
    """
    Geometry Configuration
    """
    shape_type = target.shape_type
    cls = FUDGEO_GEOMETRY_LOOKUP[shape_type][target.has_z, target.has_m]
    filter_types = SHAPELY_GEOMETRY_LOOKUP[shape_type]
    combiner = _get_combiner(filter_types)
    return GeometryConfig(
        geometry_cls=cls, is_multi=target.is_multi_part,
        filter_types=filter_types, combiner=combiner,
        srs_id=target.spatial_reference_system.srs_id)
# End geometry_config function


def _get_combiner(filter_types: tuple) -> Callable:
    """
    Get Combiner Function
    """
    if ShapelyLineString in filter_types:
        return _combine_lines
    return _nada
# End _get_combiner function


def set_extent(feature_class: FeatureClass) -> None:
    """
    Set Extent on a Feature Class using existing, spatial index, or
    geometry extents.
    """
    try:
        feature_class.extent = extent_from_feature_class(feature_class)
    except OperationsError:  # pragma: no cover
        return
# End set_extent function


def _extent_from_index_or_geometry(feature_class: FeatureClass) -> EXTENT:
    """
    Get the Extent from the Spatial Index, fail over to the extent derived
    from geometries.
    """
    extent = _extent_from_spatial_index(feature_class)
    if isfinite(extent).all():
        return extent
    else:  # pragma: no cover
        return get_extent(feature_class)
# End _extent_from_index_or_geometry function


def extent_from_feature_class(feature_class: FeatureClass) -> EXTENT:
    """
    Returns the extent from a feature class, use the extent if it has
    been set, if not check the spatial index extent, failing over to
    brute force check of all features.
    """
    extent = feature_class.extent
    if isfinite(extent).all():
        return extent
    extent = _extent_from_index_or_geometry(feature_class)
    if isfinite(extent).all():
        return extent
    else:  # pragma: no cover
        raise OperationsError(
            f'{feature_class.name} is empty or only contains empty geometries')
# End extent_from_feature_class function


def _extent_from_spatial_index(feature_class: FeatureClass) -> EXTENT:
    """
    Extent from Spatial Index
    """
    empty = nan, nan, nan, nan
    if not feature_class.has_spatial_index:  # pragma: no cover
        return empty
    cursor = feature_class.geopackage.connection.execute(f"""
        SELECT MIN(minx) AS MIN_X, MIN(miny) AS MIN_Y, 
               MAX(maxx) AS MAX_X, MAX(maxy) AS MAX_Y
        FROM {feature_class.spatial_index_name}""")
    extent = cursor.fetchone()
    if not extent:  # pragma: no cover
        return empty
    if None in extent:  # pragma: no cover
        return empty
    return extent
# End _extent_from_spatial_index function


def get_geometry_dimension(feature_class: FeatureClass) -> int:
    """
    Get Geometry Dimension
    """
    shape_type = feature_class.shape_type
    if shape_type in (GeometryType.point, GeometryType.multi_point):
        return 0
    elif shape_type in (GeometryType.linestring, GeometryType.multi_linestring):
        return 1
    elif shape_type in (GeometryType.polygon, GeometryType.multi_polygon):
        return 2
    return -1
# End get_geometry_dimension function


def check_dimension(a: int, name_a: str, b: int, name_b: str) -> None:
    """
    Check integers representing geometry dimension, current implementation
    is that b must be same or higher dimension than a, or in more concrete
    terms, the operator must have same or higher dimension than source.
    """
    if b >= a:
        return
    dim_type = {0: GeometryType.point,
                1: GeometryType.linestring,
                2: GeometryType.polygon}
    raise OperationsError(
        f'Geometry dimension mismatch, cannot overlay '
        f'{name_a} {dim_type[a]} with {name_b} {dim_type[b]}')
# End check_dimension function


if __name__ == '__main__':  # pragma: no cover
    pass
