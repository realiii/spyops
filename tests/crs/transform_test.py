# -*- coding: utf-8 -*-
"""
Tests for Transformation Helpers
"""


from os.path import pathsep
from pathlib import Path
from warnings import simplefilter, catch_warnings

from pyproj import CRS, Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.datadir import append_data_dir, get_data_dir, set_data_dir
from pytest import mark, raises

from spyops.crs.transform import (
    get_transform_best_guess, get_transforms, _validate_crs_for_transform,
    _validate_aoi_for_crs, _make_boxes)
from spyops.shared.exception import (
    CoordinateSystemNotSupportedError,
    InvalidAreaOfInterestError, NoValidTransformerError, OperationsWarning)


pytestmark = [mark.crs]


GRID_PATH: Path = Path(__file__).parent.parent.parent.joinpath('grids')


def use_grids(flag: bool) -> None:
    """
    Uses sync'd local grids in tests for transforms or disables them
    """
    if flag:
        if GRID_PATH.is_dir():
            append_data_dir(str(GRID_PATH))
    else:
        set_data_dir(get_data_dir().split(pathsep)[0])
# End use_grids function


class UseGrids:
    """
    Use Grids
    """
    def __init__(self, flag: bool) -> None:
        """
        Initialize the UseGrids class
        """
        super().__init__()
        self._flag: bool = flag
    # End init built-in

    def __enter__(self) -> 'UseGrids':
        """
        Enter
        """
        use_grids(self._flag)
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit
        """
        use_grids(False)
        return False
    # End exit built-in
# End UseGrids class


@mark.parametrize('from_code, to_code, aoi, check_validity, expected, is_best, flag, throw', [
    (26714, 9311, None, False, 1, True, False, None),  # conversion only
    (26714, 32164, None, False, 1, False, False, None),  # transform, no grids
    (26714, 32164, None, False,  5, True, True, None),  # transform with grids
    (4326, 2964, None, False, 8, False, False, None),  # transform, no grids
    (4326, 2964, None, False, 10, True, True, None),  # transform with grids
    (26714, 26714, None, False, -1, True, False, None),  # same crs
    (5336, 5712, None, False, 0, True, False, CoordinateSystemNotSupportedError),  # vertical
    (32098, 2307, None, False, -1, True, False, NoValidTransformerError),  # no xforms
    (32600, 6826, None, False, -1, True, False, NoValidTransformerError),  # Index error
    (4745, 5224, None, False, 1, False, False, None),  # xforms as of 3.7.0 pyproj
    (4745, 5224, None, False, 2, True, True, None),  # xforms as of 3.7.0 pyproj
    (26714, 9311, AreaOfInterest(-100, 30, -101, 31), False, 1, True, False, None),  # good aoi
    (26714, 9311, AreaOfInterest(-104, 30, -95, 31), False, 1, True, False, None),  # so so aoi
    (26714, 9311, AreaOfInterest(-114, 30, -110, 31), False, 0, True, False, InvalidAreaOfInterestError),  # ng aoi
    (26714, 32164, AreaOfInterest(-100, 30, -101, 31), False, 1, False, False, None),  # good aoi, no grids
    (26714, 32164, AreaOfInterest(-100, 30, -101, 31), False, 3, True, True, None),  # good aoi with grids
    (26714, 32164, AreaOfInterest(-104, 30, -95, 31), False, 1, False, False, None),  # so so aoi, no grids
    (26714, 32164, AreaOfInterest(-104, 30, -95, 31), False, 3, True, True, None),  # so so aoi with grids
    (26714, 32164, AreaOfInterest(-114, 30, -110, 31), False, 0, True, False, InvalidAreaOfInterestError),  # ng aoi
    (26714, 9311, None, True, 1, True, False, None),  # conversion only
    (26714, 32164, None, True, 1, False, False, None),  # transform, no grids
    (26714, 32164, None, True, 5, True, True, None),  # transform with grids
    (4326, 2964, None, True, 8, False, False, None),  # transform, no grids
    (4326, 2964, None, True, 10, True, True, None),  # transform with grids
    (26714, 26714, None, True, -1, True, False, None),  # same crs
    (5336, 5712, None, True, 0, True, False, CoordinateSystemNotSupportedError),  # vertical
    (32098, 2307, None, True, -1, True, False, NoValidTransformerError),  # no xforms
    (32600, 6826, None, True, -1, True, False, NoValidTransformerError),  # Index error
    (4745, 5224, None, True, 1, False, False, None),  # xforms as of pyproj 3.7.0
    (4745, 5224, None, True, 2, True, True, None),  # xforms as of pyproj 3.7.0
    (26714, 9311, AreaOfInterest(-100, 30, -101, 31), True, 1, True, False, None),  # good aoi
    (26714, 9311, AreaOfInterest(-104, 30, -95, 31), True, 1, True, False, None),  # so so aoi
    (26714, 9311, AreaOfInterest(-114, 30, -110, 31), True, 0, True, False, InvalidAreaOfInterestError),  # ng aoi
    (26714, 32164, AreaOfInterest(-100, 30, -101, 31), True, 1, False, False, None),  # good aoi, no grids
    (26714, 32164, AreaOfInterest(-100, 30, -101, 31), True, 1, False, True, None),  # good aoi with grids
    (26714, 32164, AreaOfInterest(-104, 30, -95, 31), True, 1, False, False, None),  # so so aoi, no grids
    (26714, 32164, AreaOfInterest(-104, 30, -95, 31), True, 1, False, True, None),  # so so aoi with grids
    (26714, 32164, AreaOfInterest(-114, 30, -110, 31), True, 0, True, False, InvalidAreaOfInterestError),  # ng aoi
    (32665, 32065, None, False, 7, False, False, None),
    (32665, 32065, None, False, 10, True, True, None),
    (32665, 32065, None, True, 7, False, False, None),
    (32665, 32065, None, True, 10, True, True, None),
    (32665, 32065, AreaOfInterest(-90, 27, -89, 28), False, 6, True, False, None),
    (32665, 32065, AreaOfInterest(-90, 27, -89, 28), False, 7, True, True, None),
    (32665, 32065, AreaOfInterest(-90, 27, -89, 28), True, 6, True, False, None),
    (32665, 32065, AreaOfInterest(-90, 27, -89, 28), True, 6, True, True, None),
])
def test_get_transforms(from_code, to_code, aoi, check_validity,
                        expected, is_best, flag, throw):
    """
    Test getting transform object lists
    """
    with UseGrids(flag):
        crs1, crs2 = CRS(from_code), CRS(to_code)
        if throw is not None:
            with raises(throw):
                get_transforms(crs1, crs2, aoi)
            return
        is_required, _, records = get_transforms(
            source_crs=crs1, target_crs=crs2, aoi=aoi,
            check_validity=check_validity)
        if not is_required:
            assert expected == -1
            return
        assert len(records) == expected
        best, accuracy, transformer = records[0]
        assert accuracy is None or isinstance(accuracy, float)
        assert isinstance(transformer, Transformer)
        assert isinstance(best, bool)
        assert is_best is best
# End test_get_transforms function


@mark.parametrize('from_code, to_code, flag, has_warning', [
    (4326, 4326, False, False),
    (26714, 32164, False, True),
    (4267, 4326, False, True),
    (32665, 32065, False, True),
    (26714, 32164, True, True),
    (4267, 4326, True, True),
    (32665, 32065, True, True),
])
def test_get_transform_best_guess(from_code, to_code, flag, has_warning):
    """
    Test get_transform_best_guess
    """
    with catch_warnings(record=True) as ws:
        simplefilter('always')
        with UseGrids(flag):
            get_transform_best_guess(source_crs=CRS(from_code), target_crs=CRS(to_code))
            if has_warning:
                assert len(ws) == 2 - flag
                assert issubclass(ws[-1].category, OperationsWarning)
# End test_get_transform_best_guess function


@mark.parametrize('crs, expected, throw', [
    ((CRS(4326),), (CRS(4326),), None),
    ((CRS(4326), CRS(4143)), (CRS(4326), CRS(4143)), None),
    (CRS(9451), '', CoordinateSystemNotSupportedError)
])
def test_validate_crs_for_transform(crs, expected, throw):
    """
    Test CRS validation
    """
    if throw is not None:
        with raises(throw):
            _validate_crs_for_transform(crs)
    else:
        _validate_crs_for_transform(*crs)
        assert crs == expected
# End test_validate_crs_for_transform function


CUSTOM_WGS84_BRITISH_NATIONAL_GRID = ("""
    PROJCRS["WGS84 / British National Grid",
            BASEGEOGCRS["WGS 84",
                ENSEMBLE["World Geodetic System 1984 ensemble",
                    MEMBER["World Geodetic System 1984 (Transit)"],
                    MEMBER["World Geodetic System 1984 (G730)"],
                    MEMBER["World Geodetic System 1984 (G873)"],
                    MEMBER["World Geodetic System 1984 (G1150)"],
                    MEMBER["World Geodetic System 1984 (G1674)"],
                    MEMBER["World Geodetic System 1984 (G1762)"],
                    MEMBER["World Geodetic System 1984 (G2139)"],
                    ELLIPSOID["WGS 84",6378137,298.257223563,
                        LENGTHUNIT["metre",1]],
                    ENSEMBLEACCURACY[2.0]],
                PRIMEM["Greenwich",0,
                    ANGLEUNIT["degree",0.0174532925199433]],
                ID["EPSG",4326]],
        CONVERSION["British National Grid",
            METHOD["Transverse Mercator",
                ID["EPSG",9807]],
            PARAMETER["Latitude of natural origin",49,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8801]],
            PARAMETER["Longitude of natural origin",-2,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8802]],
            PARAMETER["Scale factor at natural origin",0.9996012717,
                SCALEUNIT["unity",1],
                ID["EPSG",8805]],
            PARAMETER["False easting",400000,
                LENGTHUNIT["metre",1],
                ID["EPSG",8806]],
            PARAMETER["False northing",-100000,
                LENGTHUNIT["metre",1],
                ID["EPSG",8807]]],
        CS[Cartesian,2],
            AXIS["(E)",east,
                ORDER[1],
                LENGTHUNIT["metre",1]],
            AXIS["(N)",north,
                ORDER[2],
                LENGTHUNIT["metre",1]]]    
""")


@mark.parametrize('input_crs, aoi, throw', [
    (2846, AreaOfInterest(-95, 31, -96, 30), None),
    (2846, AreaOfInterest(-108, 29, -104, 32), None),
    (2846, AreaOfInterest(-180, -90, 180, 90), None),
    (2846, AreaOfInterest(-120, 49, -119, 50), InvalidAreaOfInterestError),
    (4269, AreaOfInterest(-114, 50, -113, 51), None),
    (CUSTOM_WGS84_BRITISH_NATIONAL_GRID, None, None),
    (CUSTOM_WGS84_BRITISH_NATIONAL_GRID, AreaOfInterest(-180, 75, 180, -75), None),
])
def test_validate_aoi_for_crs(input_crs, aoi, throw):
    """
    Tests validation of AOI against CRS AOU
    """
    crs = CRS(input_crs)
    if throw is not None:
        with raises(InvalidAreaOfInterestError):
            _validate_aoi_for_crs(aoi, crs)
        return
    _validate_aoi_for_crs(aoi, crs)
# End test_validate_aoi_for_crs function


@mark.parametrize('left, right, top, bottom, count', [
    (-120, -110, 60, 50, 1),
    (-120, -180, 60, 50, 2),
])
def test_make_boxes(left, right, top, bottom, count):
    """
    Test make_boxes
    """
    assert len(_make_boxes(left, bottom, right, top)) == count
# End test_make_boxes function


if __name__ == '__main__':  # pragma: no cover
    pass
