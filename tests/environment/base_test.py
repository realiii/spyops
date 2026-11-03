# -*- coding: utf-8 -*-
"""
Tests for Base Classes
"""


from pyproj import CRS
from pytest import approx, mark, raises

from spyops.crs.constant import WGS84
from spyops.crs.util import get_crs_from_source
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.base import Extent


pytestmark = [mark.environment]


class TestExtent:
    """
    Test Processing Extent
    """
    def test_bad_polygon(self):
        """
        Test bad polygon
        """
        with raises(TypeError):
            Extent(polygon=Ellipsis, crs=WGS84)
    # End test_bad_polygon method

    def test_from_feature_class(self, world_features):
        """
        Test From Feature Class
        """
        extent = Extent.from_feature_class(world_features['admin_a'])
        assert approx(extent.bounds, abs=0.001) == (-180, -90, 180, 83.6654)
        assert extent.coordinate_reference_system == WGS84
    # End test_from_feature_class method

    def test_from_feature_classes(self, world_features):
        """
        Test From Feature Classes
        """
        transformations = ANALYSIS_SETTINGS.geographic_transformations
        extent = Extent.from_feature_classes([world_features['admin_a']], transformations)
        assert approx(extent.bounds, abs=0.001) == (-180, -90, 180, 83.6654)
        assert extent.coordinate_reference_system == WGS84
    # End test_from_feature_classes method

    @mark.parametrize('names, expected', [
        (['hydro_utm11_zm_a', 'hydro_utm11_zm_a', 'transmission_10tm_l', 'toponymy_6654_mp', 'structures_p'], (674475.882, 5652794.991, 710481.517, 5681869.218)),
        (['structures_p', 'hydro_utm11_zm_a', 'transmission_10tm_l', 'toponymy_6654_mp'], (-114.510, 50.990, -113.984, 51.259)),
        (['structures_p'], (-114.499, 51.000, -114.001, 51.249)),
    ])
    def test_from_feature_classes_mix(self, ntdb_zm_small, names, expected):
        """
        Test From Feature Classes using mixture of crs
        """
        transformations = ANALYSIS_SETTINGS.geographic_transformations
        crs = get_crs_from_source(ntdb_zm_small[names[0]])
        extent = Extent.from_feature_classes([ntdb_zm_small[name] for name in names], transformations)
        assert approx(extent.bounds, abs=0.001) == expected
        assert extent.coordinate_reference_system == crs
    # End test_from_feature_classes_mix method

    def test_from_bounds(self):
        """
        Test From Bounds
        """
        crs = CRS(4267)
        extent = Extent.from_bounds(-111, 50, -107, 60, crs)
        assert approx(extent.bounds, abs=0.001) == (-111, 50, -107, 60)
        assert extent.coordinate_reference_system == crs
    # End test_from_bounds method

    def test_empty_polygon(self):
        """
        Test empty polygon
        """
        extent = Extent(polygon=None, crs=WGS84)
        assert extent.polygon.is_empty
    # End test_empty_polygon method

    def test_equality(self):
        """
        Test equality
        """
        a = Extent.from_bounds(1, 2, 3, 4, crs=WGS84)
        b = Extent.from_bounds(1, 2, 3, 4, crs=WGS84)
        assert a == b
    # End test_equality method

    def test_truth(self):
        """
        Test truth
        """
        assert bool(Extent(None, crs=WGS84)) is False
    # End test_truth method
# End TestExtent class


if __name__ == '__main__':  # pragma: no cover
    pass
