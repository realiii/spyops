# -*- coding: utf-8 -*-
"""
Tests for Output Coordinates
"""


from pyproj import CRS

from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap


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
    assert ANALYSIS_SETTINGS.scratch_workspace is original
# End test_output_coordinate_system function


if __name__ == '__main__':  # pragma: no cover
    pass
