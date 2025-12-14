# -*- coding: utf-8 -*-
"""
Coordinate Reference System Functionality
"""


from math import nan

from fudgeo import FeatureClass
from fudgeo.util import get_extent
from numpy import isfinite
from pyproj import CRS
from pyproj.exceptions import CRSError

from geomio.shared.constants import UNSUPPORTED_WKT
from geomio.shared.hints import EXTENT
from geomio.shared.exceptions import (
    CoordinateSystemNotSupportedError, OperationsError)


def get_crs_from_source(source: CRS | FeatureClass) -> CRS:
    """
    Returns a valid CRS object from geopackage feature class or CRS object
    """
    if isinstance(source, CRS):
        return source
    srs = source.spatial_reference_system
    # NOTE although a third party can store values in spatial reference
    #  table we should "make no assumptions" per the geopackage spec
    success, crs = from_authority(
        auth_name=srs.organization, auth_code=srs.srs_id)
    if success:
        return crs
    try:
        return CRS.from_wkt(srs.definition)
    except CRSError as err:
        msg = UNSUPPORTED_WKT.format(srs.definition)
        raise CoordinateSystemNotSupportedError(f'{msg}:\n{err}')
# End get_crs_from_source function


def from_authority(auth_name: str, auth_code: str | int) \
        -> tuple[bool, CRS | str]:
    """
    Make a CRS from an authority name and code, return boolean for success
    along with CRS object or error string in the case of failure.
    """
    try:
        return True, CRS.from_authority(auth_name, auth_code)
    except CRSError as err:
        return False, str(err)
# End from_authority function


def _change_crs_dimension(source_crs: CRS, target_crs: CRS) \
        -> tuple[CRS, CRS, bool]:
    """
    Change CRS Dimensions to be internally consistent, return flag that
    indicates the transformations will include vertical.
    """
    # NOTE if source is not compound but target is compound make target 2D
    #  since we really cannot convert Z values not knowing the source VCS
    if not source_crs.is_compound and target_crs.is_compound:
        return source_crs, target_crs.to_2d(), False
    # NOTE if target is not compound but source is compound make source 2D
    #  this is a lossy operation but the user is choosing it, do not convert Z
    elif source_crs.is_compound and not target_crs.is_compound:
        return source_crs.to_2d(), target_crs, False
    # NOTE to get here we inputs both being 2D or both being 3D
    has_vertical = source_crs.is_compound and target_crs.is_compound
    return source_crs, target_crs, has_vertical
# End _change_crs_dimension function


def equals(source_crs: CRS, target_crs: CRS) -> bool:
    """
    Check if Coordinate Reference Systems are equal, account for compound crs
    adjusting to same dimension.
    """
    source_crs, target_crs, _ = _change_crs_dimension(source_crs, target_crs)
    return source_crs.equals(target_crs, ignore_axis_order=True)
# End equals function


def extent_from_feature_class(feature_class: FeatureClass) -> EXTENT:
    """
    Returns the extent from a feature class, use the extent if it has
    been set, if not check the spatial index extent, failing over to
    brute force check of all features.
    """
    extent = feature_class.extent
    if isfinite(extent).all():
        return extent
    extent = _extent_from_spatial_index(feature_class)
    if isfinite(extent).all():
        return extent
    extent = get_extent(feature_class)
    if isfinite(extent).all():
        return extent
    raise OperationsError(
        f'{feature_class.name} is empty or only contains empty geometries')
# End extent_from_feature_class function


def _extent_from_spatial_index(feature_class: FeatureClass) -> EXTENT:
    """
    Extent from Spatial Index
    """
    empty = nan, nan, nan, nan
    if not feature_class.has_spatial_index:
        return empty
    cursor = feature_class.geopackage.connection.execute(f"""
        SELECT MIN(minx) AS MIN_X, MIN(miny) AS MIN_Y, 
               MAX(maxx) AS MAX_X, MAX(maxy) AS MAX_Y
        FROM {feature_class.spatial_index_name}""")
    extent = cursor.fetchone()
    if not extent:  # pragma: no cover
        return empty
    if None in extent:  # pragma: no cover
        return empty
    return extent
# End _extent_from_spatial_index function


def check_same_crs(a: CRS | FeatureClass, b: CRS | FeatureClass) -> None:
    """
    Check Feature Classes have same CRS
    """
    if equals(get_crs_from_source(a), get_crs_from_source(b)):
        return
    raise OperationsError('CRS for input feature classes must be the same')
# End check_same_crs function


if __name__ == '__main__':  # pragma: no cover
    pass
