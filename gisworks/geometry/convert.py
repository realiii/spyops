# -*- coding: utf-8 -*-
"""
Convert Geometry
"""


from typing import Callable

from fudgeo import FeatureClass
from fudgeo.enumeration import GeometryType
from numpy import isnan, ndarray, nonzero, diff
from shapely import (
    LineString, MultiLineString, MultiPoint, MultiPolygon, Polygon, Point,
    get_rings)
from shapely.constructive import boundary
from shapely.coordinates import get_coordinates

from gisworks.geometry.constant import FUDGEO_GEOMETRY_LOOKUP
from gisworks.geometry.util import get_geoms, nada
from gisworks.shared.enumeration import OutputTypeOption
from gisworks.environment import ANALYSIS_SETTINGS


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
    src_converter = op_converter = nada
    if convert_src:
        src_converter = _as_lines
    if convert_op:
        op_converter = _as_lines
    return src_converter, op_converter
# End _use_boundary_factory function


def _as_lines(geoms: list[Polygon] | list[MultiPolygon]) \
        -> list[LineString | MultiLineString]:
    """
    Convert Polygons to LineStrings
    """
    # noinspection PyTypeChecker
    return boundary(geoms)
# End _as_lines function


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
# End get_geometry_converters function


def _find_slice_indexes(indexes: ndarray) -> tuple[int, ...]:
    """
    Find Slice Indexes, include the final index to allow for easier striding
    """
    if not len(indexes):
        return ()
    ids, = nonzero(diff(indexes))
    ids += 1
    return 0, *[int(i) for i in ids], len(indexes)
# End _find_slice_indexes function


def _update_z_values(coords: ndarray, has_z: bool) -> None:
    """
    Update Z Values if necessary
    """
    if not has_z:
        return
    z_value = ANALYSIS_SETTINGS.z_value
    if isnan(z_value):
        return
    z = coords[:, 2]
    z[isnan(z)] = z_value
# End _update_z_values function


def cast_points(geoms: list[Point], srs_id: int, has_z: bool, has_m: bool) -> list:
    """
    Cast shapely Points to fudgeo Points adjusting by including or dropping
    Z and M values if necessary.
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[GeometryType.point][has_z, has_m]
    coords = get_coordinates(geoms, include_z=has_z, include_m=has_m)
    _update_z_values(coords, has_z=has_z)
    return [cls.from_tuple(values, srs_id=srs_id) for values in coords]
# End cast_points function


def cast_multi_points(geoms: list[MultiPoint], srs_id: int,
                      has_z: bool, has_m: bool) -> list:
    """
    Cast shapely MultiPoints to fudgeo MultiPoints adjusting by including or
    dropping Z and M values if necessary.
    """
    return _cast_linear(geoms=geoms, has_z=has_z, has_m=has_m, srs_id=srs_id,
                        geom_type=GeometryType.multi_point)
# End cast_multi_points function


def cast_line_strings(geoms: list[LineString], srs_id: int,
                      has_z: bool, has_m: bool) -> list:
    """
    Cast shapely LineStrings to fudgeo LineStrings adjusting by including or
    dropping Z and M values if necessary.
    """
    return _cast_linear(geoms=geoms, has_z=has_z, has_m=has_m, srs_id=srs_id,
                        geom_type=GeometryType.linestring)
# End cast_line_strings function


def cast_multi_line_strings(geoms: list[MultiLineString], srs_id: int,
                            has_z: bool, has_m: bool) -> list:
    """
    Cast shapely MultiLineStrings to fudgeo MultiLineStrings adjusting by
    including or dropping Z and M values if necessary.
    """
    return _cast_groups(
        geoms, has_z=has_z, has_m=has_m, srs_id=srs_id,
        geom_type=GeometryType.multi_linestring, getter=get_geoms)
# End cast_multi_line_strings function


def cast_polygons(geoms: list[Polygon], srs_id: int,
                  has_z: bool, has_m: bool) -> list:
    """
    Cast shapely Polygons to fudgeo Polygons adjusting by including or dropping
    Z and M values if necessary.
    """
    return _cast_groups(
        geoms, has_z=has_z, has_m=has_m, srs_id=srs_id,
        geom_type=GeometryType.polygon, getter=get_rings)
# End cast_polygons function


def cast_multi_polygons(geoms: list[MultiPolygon], srs_id: int,
                        has_z: bool, has_m: bool) -> list:
    """
    Cast shapely MultiPolygons to fudgeo MultiPolygons adjusting by including or
    dropping Z and M values if necessary.
    """
    converted = []
    cls = FUDGEO_GEOMETRY_LOOKUP[GeometryType.multi_polygon][has_z, has_m]
    for geom in geoms:
        poly_coords = []
        for part in get_geoms(geom):
            coords, indexes = get_coordinates(
                get_rings(part), include_z=has_z, include_m=has_m,
                return_index=True)
            ids = _find_slice_indexes(indexes)
            _update_z_values(coords, has_z=has_z)
            poly_coords.append([coords[b:e] for b, e in zip(ids[:-1], ids[1:])])
        converted.append(cls(poly_coords, srs_id=srs_id))
    return converted
# End cast_multi_polygons function


def _cast_linear(geoms: list[MultiPoint] | list[LineString], has_z: bool,
                 has_m: bool, srs_id: int, geom_type: str) -> list:
    """
    Cast Linear Geometry
    """
    cls = FUDGEO_GEOMETRY_LOOKUP[geom_type][has_z, has_m]
    coords, indexes = get_coordinates(
        geoms, include_z=has_z, include_m=has_m, return_index=True)
    ids = _find_slice_indexes(indexes)
    _update_z_values(coords, has_z=has_z)
    return [cls(coords[b:e], srs_id=srs_id) for b, e in zip(ids[:-1], ids[1:])]
# End _cast_linear function


def _cast_groups(geoms: list[MultiLineString] | list[Polygon], has_z: bool,
                 has_m: bool, srs_id: int, geom_type: str,
                 getter: Callable) -> list:
    """
    Cast Groups of Geometries
    """
    converted = []
    cls = FUDGEO_GEOMETRY_LOOKUP[geom_type][has_z, has_m]
    for geom in geoms:
        # noinspection PyTypeChecker
        coords, indexes = get_coordinates(
            getter(geom), include_z=has_z, include_m=has_m, return_index=True)
        ids = _find_slice_indexes(indexes)
        _update_z_values(coords, has_z=has_z)
        converted.append(cls([coords[b:e] for b, e in
                              zip(ids[:-1], ids[1:])], srs_id=srs_id))
    return converted
# End _cast_groups function


if __name__ == '__main__':  # pragma: no cover
    pass
