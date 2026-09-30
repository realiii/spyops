# -*- coding: utf-8 -*-
"""
Make Valid Tests
"""

from pytest import mark
from shapely import from_wkt

from spyops.geometry.wa.valid import make_valid_structure

pytestmark = [mark.geometry]


class TestMakeValid:
    """
    Test Make Valid
    """
    def test_polygon(self):
        """
        Test Make Valid
        """
        a = from_wkt('Polygon ((0 0 0 0, 1 1 1 1, 0 1 2 3, 1 0 4 5, 0 0 0 0))')
        result = make_valid_structure(a)
        assert result.has_m
    # End test_polygon function

    def test_multi_linestring(self):
        """
        Test multi linestring
        """
        a = from_wkt('MULTILINESTRING ((0 0 0 0, 1 1 1 1), (0 1 2 3, 1 0 4 5))')
        result = make_valid_structure(a)
        assert result.has_m
    # End test_multi_linestring method
# End TestMakeValid class


if __name__ == '__main__':  # pragma: no cover
    pass
