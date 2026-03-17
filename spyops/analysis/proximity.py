# -*- coding: utf-8 -*-
"""
Proximity
"""


from typing import TYPE_CHECKING

from spyops.shared.enumeration import (
    BufferTypeOption, DissolveOption, EndOption, SideOption)
from spyops.shared.hint import DISTANCE, FIELDS, FIELD_NAMES, XY_TOL
from spyops.shared.keywords import (
    BUFFER_TYPE, DISSOLVE_OPTION, DISTANCE_ARG, END_OPTION, GROUP_FIELDS,
    RESOLUTION, SIDE_OPTION, SOURCE)
from spyops.validation import (
    validate_dissolve_option, validate_distance, validate_field,
    validate_overwrite_source, validate_range, validate_result,
    validate_side_option, validate_source_feature_class,
    validate_str_enumeration, validate_target_feature_class,
    validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['buffer_']


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_distance(DISTANCE_ARG, element_name=SOURCE)
@validate_side_option(SIDE_OPTION, SOURCE)
@validate_str_enumeration(END_OPTION, EndOption)
@validate_field(GROUP_FIELDS, element_name=SOURCE, exclude_primary=False,
                is_optional=True)
@validate_dissolve_option(DISSOLVE_OPTION, GROUP_FIELDS)
@validate_str_enumeration(BUFFER_TYPE, BufferTypeOption)
@validate_range(RESOLUTION, default=16, min_value=8, max_value=128, type_=int)
@validate_xy_tolerance()
@validate_overwrite_source()
def buffer_(source: 'FeatureClass', target: 'FeatureClass', distance: DISTANCE,
            *, side_option: SideOption = SideOption.FULL,
            end_option: EndOption = EndOption.ROUND,
            dissolve_option: DissolveOption = DissolveOption.NONE,
            group_fields: FIELDS | FIELD_NAMES = (),
            buffer_type: BufferTypeOption = BufferTypeOption.PLANAR,
            resolution: int = 16,
            xy_tolerance: XY_TOL = None) -> 'FeatureClass':
    """
    Buffer

    Create polygons that are buffers of the input features based on specified
    distance(s) and optional attributes.
    """
    pass
# End buffer_ function


if __name__ == '__main__':  # pragma: no cover
    pass
