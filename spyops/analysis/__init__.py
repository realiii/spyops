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
    'select',
    'split',
    'split_by_attributes',
    'table_select',
    'extract_rows',
    'extract_features',
    'erase',
    'intersect',
    'symmetrical_difference',
    'union',

    'AlgorithmOption',
    'AttributeOption',
    'OutputTypeOption',
]


if __name__ == '__main__':  # pragma: no cover
    pass
