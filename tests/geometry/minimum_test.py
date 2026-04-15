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
    (MinimumGeometryOption.RECTANGLE_BY_AREA, [
        (7.6672, 47.7143), (9.1312, 51.7268), (12.6931, 50.4272),
        (11.2291, 46.4147), (7.6672, 47.7143)]),
    (MinimumGeometryOption.RECTANGLE_BY_WIDTH, [
        (6.6286, 48.7751), (10.4148, 52.4821), (12.6748, 50.1737),
        (8.8887, 46.4667), (6.6286, 48.7751)]),
    (MinimumGeometryOption.CONVEX_HULL, [
        (7.6672, 47.7143), (8.8465, 50.9466), (12.2785, 50.5785),
        (12.5593, 50.0606), (9.5766, 47.1403), (7.6672, 47.7143)]),
    (MinimumGeometryOption.CIRCLE, [
        (7.3264, 49.0319), (7.3786, 49.5621), (7.5333, 50.0719),
        (7.7844, 50.5417), (8.1224, 50.9535), (8.5342, 51.2915),
        (9.0040, 51.5426), (9.5138, 51.6972), (10.0440, 51.7495),
        (10.5741, 51.6972), (11.0839, 51.5426), (11.5538, 51.2915),
        (11.9656, 50.9535), (12.3035, 50.5417), (12.5547, 50.0719),
        (12.7093, 49.5621), (12.7615, 49.0319), (12.7093, 48.5017),
        (12.5547, 47.9919), (12.3035, 47.5221), (11.9656, 47.1103),
        (11.5538, 46.7723), (11.0839, 46.5212), (10.5741, 46.3666),
        (10.0440, 46.3143), (9.5138, 46.3666), (9.0040, 46.5212),
        (8.5342, 46.7723), (8.1224, 47.1103), (7.7844, 47.5221),
        (7.5333, 47.9919), (7.3786, 48.5017), (7.3264, 49.0319)]),
    (MinimumGeometryOption.ENVELOPE, [
        (7.6672, 47.1403), (7.6672, 50.9466), (12.5593, 50.9466),
        (12.5593, 47.1403), (7.6672, 47.1403)]),
])
def test_geometry_minimum_line(inputs, option, expected):
    """
    Test geometry minimum for line
    """
    source = inputs['mbg_l']
    features = source.select(include_primary=True).fetchall()
    _, geoms = to_shapely(
        features, transformer=None, option=DimensionOption.TWO_D)
    func = GEOMETRY_MINIMUM[option]
    result, = func(geoms)
    coords = list(result.normalize().exterior.coords)
    assert approx(sum(coords, ()), abs=0.001) == sum(expected, ())
# End test_geometry_minimum_line function


@mark.parametrize('option, expected', [
    (MinimumGeometryOption.RECTANGLE_BY_AREA, [
        (7.6796, 47.7268), (9.1321, 51.7192), (12.7116, 50.4169),
        (11.2592, 46.4245), (7.6796, 47.7268)]),
    (MinimumGeometryOption.RECTANGLE_BY_WIDTH, [
        (6.6428, 48.7948), (10.4356, 52.4769), (12.6827, 50.1624),
        (8.8899, 46.4802), (6.6428, 48.7948)]),
    (MinimumGeometryOption.CONVEX_HULL, [
        (7.6796, 47.7268), (8.8465, 50.9342), (12.2847, 50.5722),
        (12.5843, 50.0668), (9.5891, 47.1590), (7.6796, 47.7268)]),
    (MinimumGeometryOption.CIRCLE, [
        (7.3927, 48.9422), (7.4449, 49.4724), (7.5996, 49.9822),
        (7.8507, 50.4520), (8.1887, 50.8638), (8.6005, 51.2018),
        (9.0703, 51.4529), (9.5801, 51.6076), (10.1103, 51.6598),
        (10.6405, 51.6076), (11.1503, 51.4529), (11.6201, 51.2018),
        (12.0319, 50.8638), (12.3699, 50.4520), (12.6210, 49.9822),
        (12.7757, 49.4724), (12.8279, 48.9422), (12.7757, 48.4120),
        (12.6210, 47.9022), (12.3699, 47.4324), (12.0319, 47.0206),
        (11.6201, 46.6826), (11.1503, 46.4315), (10.6405, 46.2768),
        (10.1103, 46.2246), (9.5801, 46.2768), (9.0703, 46.4315),
        (8.6005, 46.6826), (8.1887, 47.0206), (7.8507, 47.4324),
        (7.5996, 47.9022), (7.4449, 48.4120), (7.3927, 48.9422)]),
    (MinimumGeometryOption.ENVELOPE, [
        (7.6796, 47.1590), (7.6796, 50.9342), (12.5843, 50.9342),
        (12.5843, 47.1590), (7.6796, 47.1590)]),
])
def test_geometry_minimum_polygon(inputs, option, expected):
    """
    Test geometry minimum for polygon
    """
    source = inputs['mbg_a']
    features = source.select(include_primary=True).fetchall()
    _, geoms = to_shapely(
        features, transformer=None, option=DimensionOption.TWO_D)
    func = GEOMETRY_MINIMUM[option]
    result, = func(geoms)
    coords = list(result.normalize().exterior.coords)
    assert approx(sum(coords, ()), abs=0.001) == sum(expected, ())
# End test_geometry_minimum_polygon function


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
