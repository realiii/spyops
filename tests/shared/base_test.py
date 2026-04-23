# -*- coding: utf-8 -*-
"""
Tests for Base
"""

from pytest import mark
from shapely.geometry.polygon import Polygon

from spyops.shared.base import (
    AnalysisComponents, PlanarizeResults)

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
