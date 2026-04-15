# -*- coding: utf-8 -*-
"""
Test module for minimum geometry functions.
"""


from pytest import approx, mark

from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.minimum import GEOMETRY_MINIMUM, GEOMETRY_MINIMUM_ATTRS
from spyops.geometry.util import to_shapely
from spyops.shared.enumeration import MinimumGeometryOption


pytestmark = [mark.geometry]


@mark.parametrize('option, expected', [
    (MinimumGeometryOption.RECTANGLE_BY_AREA, [
        (7.6700, 47.7178), (9.1383, 51.7284), (12.6942, 50.4266),
        (11.2259, 46.4160), (7.6700, 47.7178)]),
    (MinimumGeometryOption.RECTANGLE_BY_WIDTH, [
        (6.6354, 48.7744), (10.4145, 52.4747), (12.6720, 50.1690), (8.8929, 46.4688), (6.6354, 48.7744)]),
    (MinimumGeometryOption.CONVEX_HULL, [
        (7.6700, 47.7178), (8.8511, 50.9439), (12.2666, 50.5832), (12.5597, 50.0590),
        (9.5895, 47.1508), (7.6700, 47.7178)]),
    (MinimumGeometryOption.CIRCLE,
     [(7.3454, 49.0048), (7.3975, 49.5343), (7.5519, 50.0433),
      (7.8027, 50.5125), (8.1402, 50.9237), (8.5514, 51.2612),
      (9.0206, 51.5120), (9.5296, 51.6664), (10.0591, 51.7186),
      (10.5885, 51.6664), (11.0976, 51.5120), (11.5667, 51.2612),
      (11.9780, 50.9238), (12.3154, 50.5125), (12.5662, 50.0434),
      (12.7206, 49.5343), (12.7728, 49.0049), (12.7206, 48.4755),
      (12.5662, 47.9664), (12.3154, 47.4972), (11.9780, 47.0860),
      (11.5667, 46.7485), (11.0976, 46.4978), (10.5885, 46.3433),
      (10.0591, 46.2912), (9.5297, 46.3433), (9.0206, 46.4978),
      (8.5515, 46.7485), (8.1402, 47.0860), (7.8027, 47.4972),
      (7.5520, 47.9664), (7.3976, 48.4755), (7.3454, 49.0049)]),
    (MinimumGeometryOption.ENVELOPE, [
        (7.6700, 47.1508), (7.6700, 50.9439), (12.5596, 50.9439),
        (12.5596, 47.1508), (7.6700, 47.1508)]),
])
def test_geometry_minimum_multi_point(inputs, option, expected):
    """
    Test geometry minimum for multipoint
    """
    source = inputs['mbg_mp']
    features = source.select(include_primary=True).fetchall()
    _, geoms = to_shapely(
        features, transformer=None, option=DimensionOption.TWO_D)
    func = GEOMETRY_MINIMUM[option]
    result, = func(geoms)
    coords = list(result.normalize().exterior.coords)
    assert approx(sum(coords, ()), abs=0.001) == sum(expected, ())
# End test_geometry_minimum_multi_point function


@mark.parametrize('option, expected', [
    (MinimumGeometryOption.RECTANGLE_BY_AREA, (3.7867, 4.2709, 20.1081)),
    (MinimumGeometryOption.RECTANGLE_BY_WIDTH, (3.2267, 5.2889, 45.6042)),
    (MinimumGeometryOption.CONVEX_HULL, (3.4344, 5.4165, 58.06182)),
    (MinimumGeometryOption.CIRCLE, (5.4273, 5.4273, 0.)),
    (MinimumGeometryOption.ENVELOPE, (3.7930, 4.8896, 90.)),
])
def test_geometry_minimum_attributes(inputs, option, expected):
    """
    Test geometry minimum attributes
    """
    source = inputs['mbg_mp']
    features = source.select(include_primary=True).fetchall()
    _, geoms = to_shapely(
        features, transformer=None, option=DimensionOption.TWO_D)
    func = GEOMETRY_MINIMUM[option]
    results = func(geoms)
    func = GEOMETRY_MINIMUM_ATTRS[option]
    attrs, = func(results)
    assert approx(attrs, abs=0.001) == expected
# End test_geometry_minimum_attributes function


if __name__ == '__main__':  # pragma: no cover
    pass
