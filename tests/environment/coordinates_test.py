# -*- coding: utf-8 -*-
"""
Tests for Output Coordinates
"""


from pyproj import CRS
from pytest import mark

from spyops.crs.transform import get_transform_best_guess
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap


pytestmark = [mark.environment]


def test_output_coordinate_system():
    """
    Test output coordinate system
    """
    original = ANALYSIS_SETTINGS.output_coordinate_system
    crs = CRS(4326)
    with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, crs) as s:
        assert s.cached_value is None
        assert isinstance(s.swap_value, CRS)
        assert ANALYSIS_SETTINGS.output_coordinate_system is crs
    assert ANALYSIS_SETTINGS.output_coordinate_system is original
# End test_output_coordinate_system function


def test_geographic_transformations():
    """
    Test geographic transformations
    """
    original = ANALYSIS_SETTINGS.geographic_transformations
    transformer = get_transform_best_guess(CRS(4326), CRS(3857))

    with Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, transformer) as s:
        assert s.cached_value == []
        assert isinstance(s.swap_value, list)
        assert ANALYSIS_SETTINGS.geographic_transformations == [transformer]
    assert ANALYSIS_SETTINGS.geographic_transformations is original

    with Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, [transformer]) as s:
        assert s.cached_value == []
        assert isinstance(s.swap_value, list)
        assert ANALYSIS_SETTINGS.geographic_transformations == [transformer]
    assert ANALYSIS_SETTINGS.geographic_transformations is original
# End test_geographic_transformations function


if __name__ == '__main__':  # pragma: no cover
    pass
