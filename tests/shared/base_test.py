# -*- coding: utf-8 -*-
"""
Tests for Base
"""

from fudgeo.geometry.point import PointZM
from pytest import mark
from shapely import MultiPoint
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

from geomio.shared.base import (
    AnalysisComponents, GeometryConfig, PlanarizeResults)

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


def test_geometry_config_creation():
    """
    Test GeometryConfig
    """
    oc = GeometryConfig(
        fudgeo_cls=PointZM, is_multi=False,
        filter_types=(Point, MultiPoint), srs_id=4326, combiner=lambda x: x
    )
    assert oc.fudgeo_cls is PointZM
    assert oc.is_multi is False
    assert oc.filter_types == (Point, MultiPoint)
    assert oc.srs_id == 4326
# End test_geometry_config_creation function


def test_planarize_results():
    """
    Test Planarize Results
    """
    pr = PlanarizeResults([Polygon()], [Polygon()], [1])
    assert pr.planarized == [Polygon()]
    assert pr.polygons == [Polygon()]
    assert pr.ids == [1]
# End test_planarize_results function


if __name__ == '__main__':  # pragma: no cover
    pass
