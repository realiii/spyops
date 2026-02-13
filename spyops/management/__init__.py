# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.management.feature_class import (
    create_feature_class, recalculate_feature_class_extent)
from spyops.management.features import (
    delete_features, explode, multipart_to_singlepart)
from spyops.management.fields import (
    add_field, alter_field, calculate_field, delete_field)
from spyops.management.general import copy, delete
from spyops.management.indexes import (
    add_attribute_index, add_spatial_index, remove_attribute_index,
    remove_spatial_index)
from spyops.management.table import (
    create_table, delete_rows, get_count, truncate_table)


__all__ = [
    'multipart_to_singlepart',
    'explode',
    'add_spatial_index',
    'remove_spatial_index',
    'get_count',
    'create_table',
    'copy',
    'recalculate_feature_class_extent',
    'delete',
    'delete_rows',
    'delete_features',
    'truncate_table',
    'add_attribute_index',
    'remove_attribute_index',
    'delete_field',
    'add_field',
    'calculate_field',
    'create_feature_class',
    'alter_field',
]


if __name__ == '__main__':  # pragma: no cover
    pass
