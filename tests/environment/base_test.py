# -*- coding: utf-8 -*-
"""
Tests for Base Classes
"""


from pyproj import CRS
from pytest import approx, mark, raises

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
            Extent(polygon=Ellipsis, crs=CRS(4326))
    # End test_bad_polygon method

    def test_from_feature_class(self, world_features):
        """
        Test From Feature Class
        """
        extent = Extent.from_feature_class(world_features['admin_a'])
        assert approx(extent.bounds, abs=0.001) == (-180, -90, 180, 83.6654)
        assert extent.coordinate_reference_system == CRS(4326)
    # End test_from_feature_class method

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
        extent = Extent(polygon=None, crs=CRS(4326))
        assert extent.polygon.is_empty
    # End test_empty_polygon method

    def test_equality(self):
        """
        Test equality
        """
        a = Extent.from_bounds(1, 2, 3, 4, crs=CRS(4326))
        b = Extent.from_bounds(1, 2, 3, 4, crs=CRS(4326))
        assert a == b
    # End test_equality method

    def test_truth(self):
        """
        Test truth
        """
        assert bool(Extent(None, crs=CRS(4326))) is False
    # End test_truth method
# End TestExtent class


if __name__ == '__main__':  # pragma: no cover
    pass
