# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.management.feature_class import (
    create_feature_class, recalculate_feature_class_extent)
from spyops.management.features import (
    add_xy_coordinates, calculate_geometry_attributes, check_geometry,
    copy_features, delete_features, explode, feature_envelope_to_polygon,
    feature_to_point, feature_vertices_to_points, minimum_bounding_geometry,
    multipart_to_singlepart, polygon_to_line, repair_geometry,
    split_line_at_vertices, xy_table_to_line, xy_table_to_point, xy_to_line)
from spyops.management.fields import (
    add_field, add_gps_metadata_fields, alter_field, calculate_end_time,
    calculate_field, delete_field)
from spyops.management.general import (
    copy, delete, delete_identical,
    find_identical, rename)
from spyops.management.generalization import dissolve
from spyops.management.indexes import (
    add_attribute_index, add_spatial_index, remove_attribute_index,
    remove_spatial_index)
from spyops.management.projections import define_projection, project
from spyops.management.table import (
    copy_rows, create_table, delete_rows, get_count, truncate_table)
from spyops.management.workspace import (
    create_folder, create_geopackage,
    create_sqlite_database)
from spyops.shared.enumeration import (
    FieldProperty, GeometryAttribute, GeometryCheck, GroupOption,
    LineTypeOption, MinimumGeometryOption, PointTypeOption, WeightOption)
from spyops.shared.stats import (
    Average, Avg, Concat, Concatenate, Count, First, Last, Max, Maximum, Mean,
    Median, Min, Minimum, Mode, Range, StandardDeviation, StdDev, Sum,
    Summation, Unique, Var, Variance)


__all__ = [
    'create_feature_class',
    'recalculate_feature_class_extent',

    'add_xy_coordinates',
    'calculate_geometry_attributes',
    'check_geometry',
    'copy_features',
    'delete_features',
    'explode',
    'feature_envelope_to_polygon',
    'feature_to_point',
    'feature_vertices_to_points',
    'minimum_bounding_geometry',
    'multipart_to_singlepart',
    'polygon_to_line',
    'repair_geometry',
    'split_line_at_vertices',
    'xy_table_to_line',
    'xy_table_to_point',
    'xy_to_line',

    'add_field',
    'add_gps_metadata_fields',
    'alter_field',
    'calculate_end_time',
    'calculate_field',
    'delete_field',

    'copy',
    'delete',
    'delete_identical',
    'find_identical',
    'rename',

    'dissolve',

    'add_attribute_index',
    'add_spatial_index',
    'remove_attribute_index',
    'remove_spatial_index',

    'define_projection',
    'project',

    'copy_rows',
    'create_table',
    'delete_rows',
    'get_count',
    'truncate_table',

    'create_folder',
    'create_geopackage',
    'create_sqlite_database',

    'AreaUnit',
    'FieldProperty',
    'GeometryAttribute',
    'GeometryCheck',
    'GroupOption',
    'LengthUnit',
    'LineTypeOption',
    'MinimumGeometryOption',
    'PointTypeOption',
    'WeightOption',

    'Average',
    'Avg',
    'Concat',
    'Concatenate',
    'Count',
    'First',
    'Last',
    'Max',
    'Maximum',
    'Mean',
    'Median',
    'Min',
    'Minimum',
    'Mode',
    'Range',
    'StandardDeviation',
    'StdDev',
    'Sum',
    'Summation',
    'Unique',
    'Var',
    'Variance'
]


if __name__ == '__main__':  # pragma: no cover
    pass
