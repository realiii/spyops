# -*- coding: utf-8 -*-
"""
Use Workaround Tests
"""

from pytest import mark

from spyops.geometry.wa.uwa import USE_WORKAROUNDS


pytestmark = [mark.geometry]


def test_use_workarounds():
    """
    Test USE_WORKAROUNDS
    """
    assert USE_WORKAROUNDS.transform is True
    assert USE_WORKAROUNDS.make_valid is True
    assert USE_WORKAROUNDS.simplify is True
    assert USE_WORKAROUNDS.coverage_simplify is True
    assert USE_WORKAROUNDS.polygonize_drop_m is True
    assert USE_WORKAROUNDS.polygonize_drop_z_nan is True
    assert USE_WORKAROUNDS.polygonize is True
    assert USE_WORKAROUNDS.line_interpolate_point is True
    assert USE_WORKAROUNDS.line_merge is True
    assert USE_WORKAROUNDS.set_precision is True
    assert USE_WORKAROUNDS.inconsistent_zm_source is True
    assert USE_WORKAROUNDS.point_intersection is True
    assert USE_WORKAROUNDS.point_interpolation is True
    assert USE_WORKAROUNDS.geometry_order_interpolation is True
    assert USE_WORKAROUNDS.dropped_nan_measures is True
    assert USE_WORKAROUNDS.segmentize is True
# End test_use_workarounds function


if __name__ == '__main__':  # pragma: no cover
    pass
