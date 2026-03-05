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
    repair_geometry, xy_table_to_point)
from spyops.management.fields import (
    add_field, alter_field, calculate_field, delete_field)
from spyops.management.general import copy, delete
from spyops.management.indexes import (
    add_attribute_index, add_spatial_index, remove_attribute_index,
    remove_spatial_index)
from spyops.management.table import (
    create_table, delete_rows, get_count, truncate_table)
from spyops.shared.enumeration import (
    FieldProperty, GeometryAttribute, GeometryCheck, LineTypeOption,
    WeightOption)


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
    'create_feature_class',
    'create_table',
    'delete',
    'delete_features',
    'delete_field',
    'delete_rows',
    'explode',
    'get_count',
    'multipart_to_singlepart',
    'recalculate_feature_class_extent',
    'remove_attribute_index',
    'remove_spatial_index',
    'repair_geometry',
    'truncate_table',
    'xy_table_to_point',

    'AreaUnit',
    'FieldProperty',
    'GeometryAttribute',
    'GeometryCheck',
    'LengthUnit',
    'LineTypeOption',
    'WeightOption',
]


if __name__ == '__main__':  # pragma: no cover
    pass
