# -*- coding: utf-8 -*-
"""
Extraction
"""

from typing import Callable

from fudgeo import FeatureClass, Table

from geomio.analysis.util import shared_select

from geomio.shared.constants import SOURCE, TARGET
from geomio.shared.validation import (
    validate_feature_class, validate_result, validate_table)


__all__ = ['table_select', 'select', 'extract_rows', 'extract_features']


@validate_result()
@validate_table(TARGET, exists=False)
@validate_table(SOURCE)
def table_select(source: Table, target: Table, where_clause: str = '',
                 overwrite: bool = False) -> Table:
    """
    Table Select

    Select rows from a table using a where clause (optional) and write results
    to a target table.  Optionally overwrite the target table if it exists.
    """
    return shared_select(source=source, target=target,
                         where_clause=where_clause, overwrite=overwrite)
# End table_select function


@validate_result()
@validate_feature_class(TARGET, exists=False)
@validate_feature_class(SOURCE)
def select(source: FeatureClass, target: FeatureClass, where_clause: str = '',
           overwrite: bool = False) -> FeatureClass:
    """
    Select

    Select features from a feature class using a where clause (optional) and
    write results to a target feature class.  Optionally overwrite the target
    feature class if it exists.
    """
    return shared_select(source=source, target=target,
                         where_clause=where_clause, overwrite=overwrite)
# End select function


# Aliases
extract_rows: Callable[[Table, Table, str, bool], Table] = table_select
extract_features: Callable[[FeatureClass, FeatureClass, str, bool], FeatureClass] = select


if __name__ == '__main__':  # pragma: no cover
    pass
