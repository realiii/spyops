# -*- coding: utf-8 -*-
"""
Segment Tests
"""


from fudgeo.enumeration import ShapeType
from fudgeo.geometry import LineString, MultiLineString, Polygon, MultiPolygon
from pytest import mark

from spyops.geometry.segment import GEOMETRY_SEGMENT

pytestmark = [mark.geometry]


@mark.parametrize('shape_type, geom, count', [
    (ShapeType.linestring, LineString([(0, 0), (1, 0), (1, 1), (0, 1)], srs_id=4326), 3),
    (ShapeType.multi_linestring, MultiLineString([[(0, 0), (1, 0), (1, 1), (0, 1)]], srs_id=4326), 3),
    (ShapeType.polygon, Polygon([[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)], [(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)]], srs_id=4326), 8),
    (ShapeType.multi_polygon, MultiPolygon([[[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)], [(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)]]], srs_id=4326), 8),
])
def test_segments(shape_type, geom, count):
    """
    Test segments
    """
    srs_id = geom.srs_id
    func = GEOMETRY_SEGMENT[shape_type]
    result = func([(geom, 1)], geom_cls=LineString, srs_id=srs_id)
    assert len(result) == count
# End test_segments function


if __name__ == '__main__':  # pragma: no cover
    pass
