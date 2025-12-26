# -*- coding: utf-8 -*-
"""
Tests for Base
"""

from fudgeo.geometry.point import PointZM
from pytest import mark
from shapely import MultiPoint
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

from geomio.shared.base import AnalysisComponents, OverlayConfig

pytestmark = [mark.utility]


def test_analysis_components_creation():
    """
    Test AnalysisComponents
    """
    qc = AnalysisComponents(
        has_intersection=False,
        query=None,
        target=None
    )
    assert qc.has_intersection is False
    assert qc.query is None
    assert qc.target is None
# End test_analysis_components_creation function


def test_overlay_config_creation():
    """
    Test OverlayConfig
    """
    oc = OverlayConfig(
        fudgeo_cls=PointZM, is_multi=False, shapely_multi_cls=MultiPoint,
        shapely_types=(Point, MultiPoint), geometry=Polygon(), srs_id=4326
    )
    assert oc.fudgeo_cls is PointZM
    assert oc.is_multi is False
    assert oc.shapely_multi_cls is MultiPoint
    assert oc.shapely_types == (Point, MultiPoint)
    assert oc.geometry.is_empty
    assert oc.srs_id == 4326
# End test_overlay_config_creation function


if __name__ == '__main__':  # pragma: no cover
    pass
