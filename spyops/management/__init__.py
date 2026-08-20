# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.management.feature_class import (
    create_feature_class, recalculate_feature_class_extent)
from spyops.management.features import (
    add_xy_coordinates, adjust_3d_z, calculate_geometry_attributes,
    check_geometry, copy_features, delete_features, explode,
    feature_envelope_to_polygon, feature_to_line, feature_to_point,
    feature_to_polygon, feature_vertices_to_points, minimum_bounding_geometry,
    multipart_to_singlepart, points_to_line, polygon_to_line, repair_geometry,
    split_line_at_vertices, xy_table_to_line, xy_table_to_point, xy_to_line)
from spyops.management.fields import (
    add_field, add_gps_metadata_fields, alter_field, calculate_end_time,
    calculate_field, delete_field, field_statistics_to_table, reclassify_field,
    standardize_field, transform_field)
from spyops.management.general import (
    copy, delete, delete_identical, find_identical, rename, sort)
from spyops.management.generalization import dissolve
from spyops.management.indexes import (
    add_attribute_index, add_spatial_index, remove_attribute_index,
    remove_spatial_index)
from spyops.management.projections import define_projection, project
from spyops.management.sampling import (
    generate_points_along_lines, generate_transects_along_lines)
from spyops.management.table import (
    copy_rows, create_table, delete_rows, get_count, truncate_table)
from spyops.management.workspace import (
    create_folder, create_geopackage, create_sqlite_database)
from spyops.shared.enumeration import (
    AttributeSource, DistanceTypeOption, FieldProperty, GeometryAttribute,
    GeometryCheck, GroupOption, LineTypeOption, MinimumGeometryOption,
    PlacementOption, PointTypeOption, SpatialSortOption,
    StandardDeviationOptions, StandardizationMethod, StatisticOutputOption,
    TransformationMethod, WeightOption)
from spyops.shared.reclass import (
    DefinedIntervalReclass, EqualIntervalReclass, ManualReclass,
    NaturalBreaksReclass, QuantileReclass, StandardDeviationReclass,
    UniqueValuesReclass)
from spyops.shared.sort import Ascending, Descending
from spyops.shared.stats import (
    Average, Avg, CV, CoefficientOfVariation, Concat, Concatenate, Count,
    CountNonNull, CountNull, CountOutlier, First, FirstQuartile, IQR,
    InterquartileRange, Kurt, Kurtosis, Last, Least, LeastCommon, Max, Maximum,
    Mean, Median, Min, Minimum, Mode, Most, MostCommon, Outliers, Q1, Q3, Range,
    Skew, Skewness, StandardDeviation, StdDev, Sum, Summation, ThirdQuartile,
    Unique, Var, Variance, Variation)


__all__ = [
    'create_feature_class',
    'recalculate_feature_class_extent',

    'adjust_3d_z',
    'add_xy_coordinates',
    'calculate_geometry_attributes',
    'check_geometry',
    'copy_features',
    'delete_features',
    'explode',
    'feature_envelope_to_polygon',
    'feature_to_line',
    'feature_to_point',
    'feature_to_polygon',
    'feature_vertices_to_points',
    'minimum_bounding_geometry',
    'multipart_to_singlepart',
    'points_to_line',
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
    'field_statistics_to_table',
    'reclassify_field',
    'standardize_field',
    'transform_field',

    'copy',
    'delete',
    'delete_identical',
    'find_identical',
    'rename',
    'sort',

    'dissolve',

    'add_attribute_index',
    'add_spatial_index',
    'remove_attribute_index',
    'remove_spatial_index',

    'define_projection',
    'project',

    'generate_points_along_lines',
    'generate_transects_along_lines',

    'copy_rows',
    'create_table',
    'delete_rows',
    'get_count',
    'truncate_table',

    'create_folder',
    'create_geopackage',
    'create_sqlite_database',

    'AreaUnit',
    'AttributeSource',
    'DistanceTypeOption',
    'FieldProperty',
    'GeometryAttribute',
    'GeometryCheck',
    'GroupOption',
    'LengthUnit',
    'LineTypeOption',
    'MinimumGeometryOption',
    'PlacementOption',
    'PointTypeOption',
    'SpatialSortOption',
    'StandardDeviationOptions',
    'StandardizationMethod',
    'StatisticOutputOption',
    'TransformationMethod',
    'WeightOption',

    'DefinedIntervalReclass',
    'EqualIntervalReclass',
    'ManualReclass',
    'NaturalBreaksReclass',
    'QuantileReclass',
    'StandardDeviationReclass',
    'UniqueValuesReclass',

    'Ascending',
    'Descending',

    'Average',
    'Avg',
    'CV',
    'CoefficientOfVariation',
    'Concat',
    'Concatenate',
    'Count',
    'CountNonNull',
    'CountNull',
    'CountOutlier',
    'First',
    'FirstQuartile',
    'IQR',
    'InterquartileRange',
    'Kurt',
    'Kurtosis',
    'Last',
    'Least',
    'LeastCommon',
    'Max',
    'Maximum',
    'Mean',
    'Median',
    'Min',
    'Minimum',
    'Mode',
    'Most',
    'MostCommon',
    'Outliers',
    'Q1',
    'Q3',
    'Range',
    'Skew',
    'Skewness',
    'StandardDeviation',
    'StdDev',
    'Sum',
    'Summation',
    'ThirdQuartile',
    'Unique',
    'Var',
    'Variance',
    'Variation',
]


if __name__ == '__main__':  # pragma: no cover
    pass
