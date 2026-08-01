# -*- coding: utf-8 -*-
"""
Tests for Container Validation
"""

from pathlib import Path

from fudgeo import GeoPackage, MemoryGeoPackage

from pytest import mark, raises

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.validation import validate_geopackage, validate_values

pytestmark = [mark.validation]


class TestValidateGeopackage:
    """
    Test Validate GeoPackage
    """
    @mark.parametrize('exists', [
        True, False
    ])
    def test_exists(self, mem_gpkg, exists):
        """
        Test exists
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
    # End test_exists method

    @mark.parametrize('exists', [
        True, False
    ])
    def test_with_current(self, mem_gpkg, exists):
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
    # End test_with_current method
# End TestValidateGeopackage class


@mark.parametrize('type_, values, expected, throws', [
    (float, [1, 2, 3], [1., 2., 3.], False),
    (float, [1.1, 2.2, 3.3], [1.1, 2.2, 3.3], False),
    (float, None, None, True),
    (float, [], None, True),
    (float, [1, 2, None, 4], [1., 2., 4.], False),
    (int, [1, 2, 3], [1, 2, 3], False),
    (int, [1.1, 2.2, 3.3], [1, 2, 3], False),
    (int, None, None, True),
    (int, [], None, True),
    (int, [1, 2, None, 4], [1, 2, 4], False),
])
def test_validate_values(type_, values, expected, throws):
    """
    Test validate values
    """
    @validate_values('vs', type_=type_)
    def values_function(vs):
        return vs
    if throws:
        with raises(ValueError):
            values_function(values)
    else:
        assert values_function(values) == expected
# End test_validate_values function


if __name__ == '__main__':  # pragma: no cover
    pass
