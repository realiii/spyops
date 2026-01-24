# -*- coding: utf-8 -*-
"""
Coordinate Reference System Functionality
"""

from fudgeo import FeatureClass, SpatialReferenceSystem
from pyproj import CRS
from pyproj.enums import WktVersion
from pyproj.exceptions import CRSError

from spyops.crs.authority import Authority, authorities, to_authority
from spyops.crs.enumeration import InfoOption
from spyops.shared.constant import (
    BAD_SRS_DEFINITIONS, CUSTOM, CUSTOM_RANGE_START, CUSTOM_UPPER, EMPTY, NONE,
    UNABLE_TO_USE_CRS, UNDEFINED, UNSUPPORTED_WKT)
from spyops.shared.exception import (
    CoordinateSystemNotSupportedError, OperationsError)
from spyops.shared.hint import GPKG
from spyops.shared.util import safe_int


def get_crs_from_source(source: CRS | FeatureClass) -> CRS:
    """
    Returns a CRS object from a geopackage feature class or CRS object
    """
    if isinstance(source, CRS):
        return source
    srs = source.spatial_reference_system
    # NOTE although a third party can store values in spatial reference
    #  table we should "make no assumptions" per the geopackage spec
    if crs := from_authority(auth_name=srs.organization, auth_code=srs.srs_id):
        return crs
    try:
        return CRS.from_wkt(srs.definition)
    except CRSError as err:
        msg = UNSUPPORTED_WKT.format(srs.definition)
        raise CoordinateSystemNotSupportedError(f'{msg}:\n{err}')
# End get_crs_from_source function


def from_authority(auth_name: str, auth_code: str | int) -> CRS | None:
    """
    Make a CRS from an authority name and code, return boolean for success
    along with CRS object or error string in the case of failure.
    """
    try:
        return CRS.from_authority(auth_name, auth_code)
    except CRSError:
        return None
# End from_authority function


def get_crs_authority(crs: CRS, option: InfoOption) -> Authority:
    """
    Safely get authority name(s) and code(s) from CRS based on option provided.
    """
    if option == InfoOption.HORIZONTAL:
        crs = _get_crs_component(crs, use_horizontal=True)
    elif option == InfoOption.VERTICAL:
        crs = _get_crs_component(crs, use_horizontal=False)
    if (authority := to_authority(crs)) is not None:
        return authority
    return Authority.from_crs(crs)
# End get_crs_authority function


def check_same_crs(a: CRS | FeatureClass, b: CRS | FeatureClass) -> None:
    """
    Check Feature Classes have same CRS
    """
    if equals(get_crs_from_source(a), get_crs_from_source(b)):
        return
    raise OperationsError('CRS for input feature classes must be the same')
# End check_same_crs function


def _get_crs_component(crs: CRS, use_horizontal: bool) -> CRS:
    """
    Returns the original crs if not compound, the horizontal component of a
    compound crs if flag is True, the vertical component otherwise.
    """
    if not crs.is_compound:
        return crs
    if use_horizontal:
        components = [crs for crs in crs.sub_crs_list if not crs.is_vertical]
        type_ = 'horizontal'
    else:
        components = [crs for crs in crs.sub_crs_list if crs.is_vertical]
        type_ = 'vertical'
    # NOTE these cases do not exist in the proj db, but here for completeness
    err_stub = 'compound CRS not supported'
    if not len(components):
        raise CoordinateSystemNotSupportedError(f'Non-{type_} {err_stub}')
    if len(components) > 1:
        raise CoordinateSystemNotSupportedError(
            f'Multiple {type_} definitions in {err_stub}')
    crs = components[0]
    # NOTE this step added to get as much metadata onto the object as possible
    if authority := to_authority(crs):
        # NOTE should be singular here, only horizontal or only vertical
        auth_name, auth_code = authority.pretty_name_and_code()
        # NOTE check everywhere for possible CRS
        if from_auth_crs := from_authority(auth_name, auth_code=auth_code):
            return from_auth_crs
    return crs
# End _get_crs_component function


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
    adjusting to the same dimension.
    """
    source_crs, target_crs, _ = change_crs_dimension(source_crs, target_crs)
    return source_crs.equals(target_crs, ignore_axis_order=True)
# End equals function


def from_crs(crs: CRS) -> SpatialReferenceSystem:
    """
    Build a Spatial Reference System object from a CRS object
    """
    msg = UNABLE_TO_USE_CRS.format(crs.to_string())
    authority = get_crs_authority(crs, option=InfoOption.ORIGINAL)
    if not authority.is_valid:
        raise CoordinateSystemNotSupportedError(msg)
    org_name, org_code = authority.org_name_and_code()
    if (org_code := safe_int(org_code)) is None:
        raise CoordinateSystemNotSupportedError(msg)
    # NOTE changed to WKT1_GDAL for similarity to QGIS, WKT1_ESRI does not
    #  create Compound CRS on export (was just Projected). Using WKT1_GDAL
    #  here also prevents ArcGIS Pro from going poof.
    return SpatialReferenceSystem(
        crs.name, organization=org_name, org_coord_sys_id=org_code,
        definition=crs.to_wkt(version=WktVersion.WKT1_GDAL))
# End from_crs function


def validate_srs(geopackage: GPKG, srs: SpatialReferenceSystem) \
        -> SpatialReferenceSystem:
    """
    Make the Spatial Reference System valid for the target GeoPackage.  The
    main purpose for this function is to ensure that a Spatial Reference System
    defined in one GeoPackage can be used in another GeoPackage without
    encountering a collision in the SRS ID

    When working with CUSTOM Spatial Reference Systems across GeoPackages
    the SRS ID cannot be used as a globally unique identifier as can be done
    with an SRS ID from an actual authority.  This function attempts to handle
    the most common cases we have seen e.g.

      1) authority with code from EPSG
      2) authority with code from ESRI
      3) authority with code from client / customer
      4) custom spatial reference system defined by third party application

    Need to get this right because SRS ID is stored in the geometry of
    GeoPackage feature classes.
    """
    srs_id = srs.srs_id
    org_name = srs.organization
    is_builtin_auth = org_name in authorities()
    is_within_range = 0 < srs_id < CUSTOM_RANGE_START
    # NOTE return srs if this is a built-in authority within expected range
    if is_builtin_auth and is_within_range:
        return srs
    # NOTE if not a built-in authority and within range (not deemed custom)
    if not is_builtin_auth and is_within_range:
        # NOTE if srs id is present and has same org name return srs
        if _has_same_org_name(geopackage, srs_id=srs_id, organization=org_name):
            return srs
        # NOTE if srs id is not present in the built-in authorities return srs
        if not _overlaps_builtin(srs_id):
            return srs
    wkt = srs.definition or EMPTY
    if not srs.name or not wkt or wkt.casefold() in BAD_SRS_DEFINITIONS:
        return SpatialReferenceSystem(
            name=srs.name, organization=NONE, org_coord_sys_id=0,
            definition=UNDEFINED)
    return SpatialReferenceSystem(
        name=CUSTOM, organization=CUSTOM_UPPER, org_coord_sys_id=0,
        definition=wkt, srs_id=_get_srs_id(geopackage, wkt))
# End validate_srs function


def _has_same_org_name(geopackage: GPKG, srs_id: int,
                       organization: str) -> bool:
    """
    Check if SRS ID is in the table and has the same organization name
    """
    sql = """SELECT organization FROM gpkg_spatial_ref_sys WHERE srs_id = ?"""
    with geopackage.connection as cin:
        cursor = cin.execute(sql, (srs_id,))
        if not (result := cursor.fetchone()):
            return False
        org_name, = result
        return organization.strip().casefold() == org_name.strip().casefold()
# End _has_same_org_name function


def _overlaps_builtin(srs_id: int) -> bool:
    """
    Check if SRS ID overlaps the built-in authorities
    """
    for auth_name in authorities():
        if from_authority(auth_name=auth_name, auth_code=srs_id):
            return True
    return False
# End _overlaps_builtin function


def _get_srs_id(geopackage: GPKG, wkt: str) -> int:
    """
    Get SRS ID
    """
    stub = """SELECT max(srs_id) AS MAX_ID FROM gpkg_spatial_ref_sys"""
    with geopackage.connection as cin:
        cursor = cin.execute(f'{stub} WHERE definition = ?', (wkt,))
        # NOTE this unpacking works because we are using an aggregate query
        value, = cursor.fetchone()
    if value not in (None, 0):
        return value
    with geopackage.connection as cin:
        cursor = cin.execute(stub)
        value, = cursor.fetchone()
    return max(value, CUSTOM_RANGE_START) + 1
# End _get_srs_id function


if __name__ == '__main__':  # pragma: no cover
    pass
