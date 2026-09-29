# -*- coding: utf-8 -*-
"""
Set Precision Tests
"""


from warnings import catch_warnings, simplefilter

from numpy import isnan
from pytest import mark
from shapely import (
    MultiLineString, MultiPoint, MultiPolygon, from_wkt, get_coordinates)

from spyops.geometry.wa.sp import set_precision
from spyops.shared.exception import OperationsWarning


pytestmark = [mark.geometry]


@mark.parametrize('wkt, cls, expected', [
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))', None, True),
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 0 0))', None, True),
    ('LineString (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)', None, False),
    ('Point (0 0 0 0)', None, False),
    ('Polygon M ((0 0 0, 0 1 1, 1 1 3, 1 0 5, 0 0 7))', None, True),
    ('Polygon M ((0 0 0, 0 1 1, 1 1 3, 1 0 5, 0 0 0))', None, True),
    ('LineString M (0 0 0, 0 1 1, 1 1 3, 1 0 5, 0 0 7)', None, False),
    ('Point M (0 0 0)', None, False),
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))', MultiPolygon, True),
    ('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 0 0))', MultiPolygon, True),
    ('LineString (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)', MultiLineString, False),
    ('Point (0 0 0 0)', MultiPoint, False),
])
def test_set_precision_nan(wkt, cls, expected):
    """
    Test set precision -- issue in polygons where coordinate gets
    assigned a NaN measure
    """
    a = from_wkt(wkt)
    if cls:
        a = cls([a])
    with catch_warnings(record=True) as ws:
        simplefilter('always')
        result = set_precision(a, grid_size=0.001)
        assert len(ws) == int(expected)
        if expected:
            w, = ws
            assert issubclass(w.category, OperationsWarning)
    coords = get_coordinates(result, include_m=True)
    assert bool(isnan(coords[:, 2]).any()) is expected
# End test_set_precision_nan function


if __name__ == '__main__':  # pragma: no cover
    pass
