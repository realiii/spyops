# -*- coding: utf-8 -*-
"""
Tests for Base
"""

from fudgeo.geometry.point import PointZM
from pytest import mark
from shapely import MultiPoint
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

from geomio.shared.base import QueryComponents, OverlayConfig

pytestmark = [mark.utility]


def test_query_components_creation():
    """
    Test QueryComponents
    """
    qc = QueryComponents(
        use_index=True,
        has_intersection=False,
        sql_touches="SELECT * FROM touches",
        sql_outside="SELECT * FROM outside",
        sql_insert="INSERT INTO table"
    )
    assert qc.use_index is True
    assert qc.has_intersection is False
    assert qc.sql_touches == "SELECT * FROM touches"
    assert qc.sql_outside == "SELECT * FROM outside"
    assert qc.sql_insert == "INSERT INTO table"
# End test_query_components_creation function


def test_overlay_config_creation():
    """
    Test OverlayConfig
    """
    oc = OverlayConfig(
        fudgeo_cls=PointZM, is_multi=False, shapely_multi_cls=MultiPoint,
        shapely_types=(Point, MultiPoint), geometry=Polygon()
    )
    assert oc.fudgeo_cls is PointZM
    assert oc.is_multi is False
    assert oc.shapely_multi_cls is MultiPoint
    assert oc.shapely_types == (Point, MultiPoint)
    assert oc.geometry.is_empty
# End test_overlay_config_creation function


if __name__ == '__main__':  # pragma: no cover
    pass
