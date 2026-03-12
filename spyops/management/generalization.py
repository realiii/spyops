# -*- coding: utf-8 -*-
"""
Generalization Data Management
"""


from typing import TYPE_CHECKING

from spyops.shared.hint import FIELDS, FIELD_NAMES, STATS_FIELDS, XY_TOL
from spyops.shared.keywords import GROUP_FIELDS, SOURCE, STATISTICS
from spyops.validation import (
    validate_field, validate_overwrite_source, validate_result,
    validate_source_feature_class, validate_statistic_field,
    validate_target_feature_class, validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_field(GROUP_FIELDS, element_name=SOURCE, exclude_primary=False)
@validate_statistic_field(STATISTICS, element_name=SOURCE)
@validate_xy_tolerance()
@validate_overwrite_source()
def dissolve(source: 'FeatureClass', target: 'FeatureClass',
             group_fields: FIELDS | FIELD_NAMES, *,
             statistics: STATS_FIELDS | None = None, as_multi_part: bool = True,
             xy_tolerance: XY_TOL = None) -> 'FeatureClass':
    """
    Dissolve

    Aggregate features based on one or more group fields and optionally
    summarize attributes.  The as_multi_part option controls whether the
    output is a single-part or multipart feature class.
    """
    pass
# End dissolve function


if __name__ == '__main__':  # pragma: no cover
    pass
