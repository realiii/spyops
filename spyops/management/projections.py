# -*- coding: utf-8 -*-
"""
Projections and Transformations
"""


from typing import TYPE_CHECKING

from fudgeo import SpatialReferenceSystem
from pyproj import CRS
from pyproj.transformer import Transformer

from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.query.management.projections import QueryProject
from spyops.shared.keywords import COORDINATE_SYSTEM
from spyops.shared.records import select_and_transform_features
from spyops.validation import (
    validate_coordinate_system, validate_overwrite_source, validate_result,
    validate_source_feature_class, validate_target_feature_class)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['project']


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_coordinate_system(COORDINATE_SYSTEM)
@validate_overwrite_source()
def project(source: 'FeatureClass', target: 'FeatureClass', *,
            coordinate_system: CRS | SpatialReferenceSystem,
            transform: Transformer | None = None) -> 'FeatureClass':
    """
    Project

    Transform the features of a feature class into another coordinate system.
    Supports geographic and projected coordinate systems, also supports
    vertical coordinate systems.  The z values of z-aware features will be
    updated if the transform provided includes vertical transformation and the
    source coordinate system includes vertical component.

    This function ignores the settings for EXTENT, Z_VALUE, OUTPUT_Z_OPTION,
    and OUTPUT_M_OPTION. The input coordinate system and transform
    values are used to temporarily define Settings during internal processing.
    """
    with (Swap(Setting.EXTENT, None), Swap(Setting.Z_VALUE, None),
          Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.SAME),
          Swap(Setting.OUTPUT_M_OPTION, OutputMOption.SAME),
          Swap(Setting.OUTPUT_COORDINATE_SYSTEM, coordinate_system),
          Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, transform)):
        query = QueryProject(source, target=target)
        target = select_and_transform_features(query)
    return target
# End project function


if __name__ == '__main__':  # pragma: no cover
    pass
