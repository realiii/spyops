# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.analysis.extract import (
    clip, extract_features, extract_rows,
    select, split, split_by_attributes, table_select)
from spyops.analysis.overlay import (
    erase, intersect, symmetrical_difference, union)
from spyops.shared.enumeration import (
    AlgorithmOption, AttributeOption, OutputTypeOption)


__all__ = [
    'clip',
    'erase',
    'extract_features',
    'extract_rows',
    'intersect',
    'select',
    'split',
    'split_by_attributes',
    'symmetrical_difference',
    'table_select',
    'union',

    'AlgorithmOption',
    'AttributeOption',
    'OutputTypeOption',
]


if __name__ == '__main__':  # pragma: no cover
    pass
