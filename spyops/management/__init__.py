# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.management.feature_class import recalculate_feature_class_extent
from spyops.management.features import multipart_to_singlepart, explode
from spyops.management.general import copy, delete
from spyops.management.indexes import add_spatial_index, remove_spatial_index
from spyops.management.table import get_count, create_table, delete_rows


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
]


if __name__ == '__main__':  # pragma: no cover
    pass
