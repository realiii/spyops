# -*- coding: utf-8 -*-
"""
Tests for General Data Management
"""


from fudgeo import FeatureClass
from pytest import mark

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.management import copy

pytestmark = [mark.management, mark.general]


def test_copy(ntdb_zm_small, mem_gpkg):
    """
    Test copy function
    """
    source = ntdb_zm_small['hydro_zm_a']
    target_name = 'hydro_a_copy'
    with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
        result = copy(source, target_name)
    assert result is not None
    assert isinstance(result, FeatureClass)
    assert result.name == target_name
    assert len(result) == len(source)
    assert result.has_z == source.has_z
    assert result.has_m == source.has_m
    assert result.spatial_reference_system == source.spatial_reference_system
# End test_copy function


if __name__ == '__main__':  # pragma: no cover
    pass
