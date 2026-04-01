# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.management.feature_class import (
    create_feature_class, recalculate_feature_class_extent)
from spyops.management.features import (
    add_xy_coordinates, calculate_geometry_attributes, check_geometry,
    copy_features, delete_features, explode, multipart_to_singlepart,
    repair_geometry, xy_table_to_line, xy_table_to_point, xy_to_line)
from spyops.management.fields import (
    add_field, alter_field, calculate_field, delete_field)
from spyops.management.general import copy, delete, rename
from spyops.management.generalization import dissolve
from spyops.management.indexes import (
    add_attribute_index, add_spatial_index, remove_attribute_index,
    remove_spatial_index)
from spyops.management.table import (
    copy_rows, create_table, delete_rows, get_count, truncate_table)
from spyops.shared.enumeration import (
    FieldProperty, GeometryAttribute, GeometryCheck, LineTypeOption,
    WeightOption)
from spyops.shared.stats import (
    Average, Avg, Concat, Concatenate, Count, First, Last, Max, Maximum, Mean,
    Median, Min, Minimum, Mode, Range, StandardDeviation, StdDev, Sum,
    Summation, Unique, Var, Variance)


__all__ = [
    'add_attribute_index',
    'add_field',
    'add_spatial_index',
    'add_xy_coordinates',
    'alter_field',
    'calculate_field',
    'calculate_geometry_attributes',
    'check_geometry',
    'copy',
    'copy_features',
    'copy_rows',
    'create_feature_class',
    'create_table',
    'delete',
    'delete_features',
    'delete_field',
    'delete_rows',
    'dissolve',
    'explode',
    'get_count',
    'multipart_to_singlepart',
    'recalculate_feature_class_extent',
    'remove_attribute_index',
    'remove_spatial_index',
    'rename',
    'repair_geometry',
    'truncate_table',
    'xy_table_to_point',
    'xy_table_to_line',
    'xy_to_line',

    'AreaUnit',
    'FieldProperty',
    'GeometryAttribute',
    'GeometryCheck',
    'LengthUnit',
    'LineTypeOption',
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
