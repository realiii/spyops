# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.management.features import multipart_to_singlepart, explode
from spyops.management.general import copy
from spyops.management.indexes import add_spatial_index, remove_spatial_index
from spyops.management.table import get_count, create_table


__all__ = [
    'multipart_to_singlepart',
    'explode',
    'add_spatial_index',
    'remove_spatial_index',
    'get_count',
    'create_table',
    'copy',
]


if __name__ == '__main__':  # pragma: no cover
    pass
