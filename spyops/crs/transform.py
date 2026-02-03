# -*- coding: utf-8 -*-
"""
Transformation Helpers
"""


from functools import partial
from typing import Callable, Optional, TYPE_CHECKING, Union

from numpy import array, isfinite
from pyproj import CRS, Transformer
from pyproj.transformer import TransformerGroup
from shapely.creation import box

from spyops.crs.base import TransformOptions, TransformOption
from spyops.crs.enumeration import InfoOption
from spyops.crs.util import (
    change_crs_dimension, equals, get_crs_authority, get_crs_from_source)
from spyops.geometry.transform import GEOMETRY_TRANSFORM
from spyops.shared.constant import (
    CRS_REQUIRED, HAS_M_KEY, HAS_Z_KEY, INCLUDE_VERTICAL_KEY, INVALID_AOI,
    NO_TRANSFORMER, TRANSFORMER_KEY, UNSUPPORTED_CRS)
from spyops.shared.exception import (
    CoordinateSystemNotSupportedError, InvalidAreaOfInterestError,
    NoValidTransformerError)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, SpatialReferenceSystem
    from shapely import Polygon
    from pyproj.aoi import AreaOfInterest


def get_transforms(source_crs: Union[CRS, 'FeatureClass', 'SpatialReferenceSystem'],
                   target_crs: Union[CRS, 'FeatureClass', 'SpatialReferenceSystem'],
                   aoi: Optional['AreaOfInterest'] = None,
                   check_validity: bool = True) -> TransformOptions:
    """
    Retrieve the available transformation options for converting coordinates
    between two coordinate reference systems (CRS). The function evaluates the
    appropriate transformation methods using the provided source and target
    CRS, with the ability to incorporate an optional area of interest (AOI)
    to refine the transformations.  The optional AOI is for the source CRS.

    Use of AOI has been seen to reduce the number of transformations returned
    but not always in a good way, that is, it may exclude a better option.

    The check_validity parameter is used to filter out transformers that
    are not valid (do not produce finite values) for the input AOI.  This
    can sometimes exclude better transformations.

    Results from this function will change depending on whether or not the
    data directory for pyproj is set.  Use the `configure_grids` function to
    set the data directory to where the grids are stored.

    Returns a TransformOptions object containing a flag indicating if a
    transformation is required, the best available transformer, and a
    list of all transformers (including the best).  If no transformer is
    required, the best will be None and options will be empty.
    """
    source_crs = get_crs_from_source(source_crs)
    target_crs = get_crs_from_source(target_crs)
    _validate_crs_for_transform(source_crs, target_crs)
    source_crs, target_crs = change_crs_dimension(source_crs, target_crs)
    if equals(source_crs, target_crs):
        return TransformOptions(is_required=False, best=None, options=[])
    _validate_aoi_for_crs(aoi, source_crs)
    msg = NO_TRANSFORMER.format(
        source_crs.name, source_crs.srs, target_crs.name, target_crs.srs)
    try:
        group = TransformerGroup(
            crs_from=source_crs, crs_to=target_crs,
            always_xy=True, area_of_interest=aoi)
    except IndexError:
        raise NoValidTransformerError(msg)
    if not len(group.transformers):
        raise NoValidTransformerError(msg)
    options = []
    best_available = group.best_available
    for i, transformer in enumerate(group.transformers):
        if (accuracy := transformer.accuracy) < 0:
            accuracy = None
        is_best = best_available and not bool(i)
        options.append(TransformOption(
            is_best=is_best, accuracy=accuracy, transformer=transformer))
    if check_validity:
        options = _check_transforms(aoi, options=options)
    if not len(options):
        raise NoValidTransformerError(msg)
    best = next((r.transformer for r in options if r.is_best), None)
    return TransformOptions(is_required=True, best=best, options=options)
# End get_transforms function


def get_transform_best_guess(source_crs: CRS, target_crs: CRS) -> Transformer | None:
    """
    Get Transformer for the best available guess between the source CRS
    and target CRS.  It will either be None if no transformation is required,
    None if source CRS and target CRS are considered equal, the best available
    transformer, or the first transformer in the list of available transformers.
    """
    if equals(source_crs, target_crs):
        return None
    is_required, best, options = get_transforms(
        source_crs, target_crs, check_validity=False)
    if not is_required or best:
        return best
    first, *_ = options
    return first.transformer
# End get_transform_best_guess function


def make_transformer_function(shape_type: str, has_z: bool, has_m: bool,
                              transformer: Transformer | None) \
        -> Callable | None:
    """
    Make Transformer Function
    """
    if transformer is None:
        return None
    include_vertical = (has_z and
                        transformer.source_crs.is_compound and
                        transformer.target_crs.is_compound)
    kwargs = {TRANSFORMER_KEY: transformer,
              INCLUDE_VERTICAL_KEY: include_vertical,
              HAS_Z_KEY: has_z, HAS_M_KEY: has_m}
    geom_transform = GEOMETRY_TRANSFORM[shape_type]
    return partial(geom_transform, **kwargs)
# End make_transformer_function function


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
        return [box(xmin=left, ymin=bottom, xmax=180, ymax=top, ccw=False),
                box(xmin=-180, ymin=bottom, xmax=right, ymax=top, ccw=False)]
    return [box(xmin=left, ymin=bottom, xmax=right, ymax=top, ccw=False)]
# End _make_boxes function


def _check_transforms(aoi: Optional['AreaOfInterest'],
                      options: list[TransformOption]) -> list[TransformOption]:
    """
    Check transforms against an Area of Interest, return only those that
    produce finite values for the AOI, this can sometimes exclude better
    transformation options, use with care.
    """
    if not aoi:
        return options
    xs = array([aoi.west_lon_degree, aoi.east_lon_degree,
                aoi.west_lon_degree, aoi.east_lon_degree], dtype=float)
    ys = array([aoi.north_lat_degree, aoi.north_lat_degree,
                aoi.south_lat_degree, aoi.south_lat_degree], dtype=float)
    if not isfinite(xs).all() or not isfinite(ys).all():  # pragma: no cover
        return options
    checked = []
    for record in options:
        x, y = record.transformer.transform(xs, ys)
        if not isfinite(x).all() or not isfinite(y).all():
            continue
        checked.append(record)
    return checked
# End _check_transforms function


if __name__ == '__main__':  # pragma: no cover
    pass
