# -*- coding: utf-8 -*-
"""
Convert Geometry
"""


from typing import Callable

from fudgeo import FeatureClass
from fudgeo.enumeration import GeometryType
from shapely import (
    LineString, MultiLineString, MultiPolygon, Polygon, boundary)

from gisworks.geometry.util import nada
from gisworks.shared.enumeration import OutputTypeOption


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


if __name__ == '__main__':  # pragma: no cover
    pass
