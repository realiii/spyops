# -*- coding: utf-8 -*-
"""
Transformation Helpers
"""


from typing import Optional, TYPE_CHECKING

from numpy import array, isfinite
from pyproj import CRS
from pyproj.transformer import TransformerGroup
from shapely.creation import box

from spyops.crs.base import TransformerRecord
from spyops.crs.enumeration import InfoOption
from spyops.crs.util import change_crs_dimension, equals, get_crs_authority
from spyops.shared.constant import (
    CRS_REQUIRED, INVALID_AOI, NO_TRANSFORMER, UNSUPPORTED_CRS)
from spyops.shared.exception import (
    CoordinateSystemNotSupportedError, InvalidAreaOfInterestError,
    NoValidTransformerError)


if TYPE_CHECKING:  # pragma: no cover
    from shapely import Polygon
    from pyproj.aoi import AreaOfInterest


def get_transforms(source_crs: CRS, target_crs: CRS,
                   aoi: Optional['AreaOfInterest'] = None,
                   check_transforms: bool = True) \
        -> tuple[bool, bool, list[TransformerRecord]]:
    """
    Returns a list of possible transformations for the source and target CRS.
    If no transform is required, return None.  Optional AOI is for source.
    """
    _validate_crs_for_transform(source_crs, target_crs)
    (source_crs, target_crs,
     has_vertical) = change_crs_dimension(source_crs, target_crs)
    if equals(source_crs, target_crs):
        return False, has_vertical, []
    _validate_aoi_for_crs(aoi, source_crs)
    msg = NO_TRANSFORMER.format(
        source_crs.name, source_crs.srs, target_crs.name, target_crs.srs)
    try:
        trans_group = TransformerGroup(crs_from=source_crs, crs_to=target_crs,
                                       always_xy=True, area_of_interest=aoi)
    except IndexError:
        raise NoValidTransformerError(msg)
    if not len(trans_group.transformers):
        raise NoValidTransformerError(msg)
    records = []
    best_available = trans_group.best_available
    for i, transform in enumerate(trans_group.transformers):
        if transform.accuracy < 0:
            accuracy = f'Unknown Accuracy'
        else:
            accuracy = f'\u00B1{transform.accuracy:.2f}m'
        label = f'{transform.description} [{accuracy}]'
        is_best = best_available and not bool(i)
        records.append(TransformerRecord(
            is_best=is_best, transform=transform, label=label))
    if check_transforms:
        records = _check_transforms(aoi, records)
    if not len(records):
        raise NoValidTransformerError(msg)
    return True, has_vertical, records
# End get_transforms function


def _validate_crs_for_transform(*args: CRS) -> None:
    """
    Ensures that the passed CRS objects are suitable to be used to gather
    transformer objects.
    """
    for crs in args:
        if not isinstance(crs, CRS):  # pragma: no cover
            raise TypeError(CRS_REQUIRED)
        if crs.is_vertical and not crs.is_compound:
            authority = get_crs_authority(crs, option=InfoOption.ORIGINAL)
            raise CoordinateSystemNotSupportedError(
                UNSUPPORTED_CRS.format(*authority.pretty_name_and_code()))
# End _validate_crs_for_transform function


def _validate_aoi_for_crs(aoi: Optional['AreaOfInterest'], crs: CRS) -> None:
    """
    Checks the aoi to see if it intersects with the AreaOfUse of the source
    """
    if aoi is None:
        return
    if crs.area_of_use is None:
        return
    aoi_boxes = _make_boxes(
        left=aoi.west_lon_degree, bottom=aoi.south_lat_degree,
        right=aoi.east_lon_degree, top=aoi.north_lat_degree)
    crs_boxes = _make_boxes(*crs.area_of_use.bounds)
    results = []
    for aoi_box in aoi_boxes:
        results.extend(aoi_box.intersects(crs_boxes))
    if not any(results):
        raise InvalidAreaOfInterestError(INVALID_AOI.format(crs.name))
# End _validate_aoi_for_crs function


def _make_boxes(left: float, bottom: float,
                right: float, top: float) -> list['Polygon']:
    """
    Make Boxes, accounting for 180/-180
    """
    if left > right:
        return [box(left, bottom, 180, top), box(-180, bottom, right, top)]
    return [box(left, bottom, right, top)]
# End _make_boxes function


def _check_transforms(aoi: Optional['AreaOfInterest'],
                      records: list[TransformerRecord]) \
        -> list[TransformerRecord]:
    """
    Check transforms against an Area of Interest, return only those that
    produce finite values.
    """
    if not aoi:
        return records
    xs = array([aoi.west_lon_degree, aoi.east_lon_degree,
                aoi.west_lon_degree, aoi.east_lon_degree], dtype=float)
    ys = array([aoi.north_lat_degree, aoi.north_lat_degree,
                aoi.south_lat_degree, aoi.south_lat_degree], dtype=float)
    if not isfinite(xs).all() or not isfinite(ys).all():  # pragma: no cover
        return records
    checked = []
    for record in records:
        x, y = record.transform.transform(xs, ys)
        if not isfinite(x).all() or not isfinite(y).all():
            continue
        checked.append(record)
    return checked
# End _check_transforms function


if __name__ == '__main__':  # pragma: no cover
    pass
