# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.management.features import multipart_to_singlepart, explode
from spyops.management.indexes import add_spatial_index


__all__ = [
    'multipart_to_singlepart',
    'explode',
    'add_spatial_index',
]


if __name__ == '__main__':  # pragma: no cover
    pass
