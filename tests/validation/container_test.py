# -*- coding: utf-8 -*-
"""
Tests for Container Validation
"""

from pathlib import Path

from fudgeo import GeoPackage, MemoryGeoPackage

from pytest import mark, raises

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.validation import validate_geopackage


pytestmark = [mark.validation]


@mark.parametrize('exists', [
    True, False
])
def test_validate_geopackage(mem_gpkg, exists):
    """
    Test validate_geopackage
    """
    @validate_geopackage('gpkg', exists=exists)
    def geo_function(gpkg):
        pass
    with raises(TypeError):
        geo_function(None)
    if exists:
        with raises(ValueError):
            geo_function(GeoPackage(Path.home()))
    geo_function(mem_gpkg)
    geo_function(MemoryGeoPackage.create())
# End test_validate_geopackage function


@mark.parametrize('exists', [
    True, False
])
def test_validate_geopackage_with_current(mem_gpkg, exists):
    """
    Test validate geopackage where current-workspace is used
    """
    @validate_geopackage(exists=exists)
    def geo_function(geopackage):
        return geopackage
    with raises(TypeError):
        geo_function(None)
    assert geo_function(mem_gpkg) is mem_gpkg
    with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
        assert geo_function(None) is mem_gpkg
    with raises(TypeError):
        with Swap(Setting.CURRENT_WORKSPACE, None):
            geo_function(None)
# End test_validate_geopackage_with_current function


if __name__ == '__main__':  # pragma: no cover
    pass
