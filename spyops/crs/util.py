# -*- coding: utf-8 -*-
"""
Coordinate Reference System Functionality
"""


from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Union

from fudgeo import SpatialReferenceSystem
from numpy import isfinite
from pyproj import CRS, Transformer
from pyproj.crs import ProjectedCRS
from pyproj.crs.coordinate_operation import AzimuthalEquidistantConversion
from pyproj.enums import WktVersion
from pyproj.datadir import append_data_dir
from pyproj.exceptions import CRSError
from pyproj.network import set_network_enabled
from shapely.creation import box
from shapely.ops import transform

from spyops.crs.authority import Authority, authorities, to_authority
from spyops.crs.constant import (
    BAD_SRS_DEFINITIONS, CUSTOM, CUSTOM_RANGE_START, CUSTOM_UPPER, NONE,
    UNDEFINED)
from spyops.crs.enumeration import InfoOption
from spyops.crs.message import UNABLE_TO_USE_CRS, UNSUPPORTED_WKT
from spyops.geometry.extent import extent_from_index_or_geometry
from spyops.shared.constant import EMPTY
from spyops.shared.exception import (
    CoordinateSystemDifferentError, CoordinateSystemNotSupportedError)
from spyops.shared.hint import EXTENT, GPKG
from spyops.shared.util import safe_int


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from numpy import ndarray
    from shapely import Polygon, Point


def configure_grids(data_path: Path | str | None = None,
                    network_enabled: bool | None = False) -> None:
    """
    Configure grids, optionally enabling network access.
    """
    set_network_enabled(active=network_enabled)
    if not data_path:
        return
    data_path = Path(data_path)
    if isinstance(data_path, Path) and data_path.is_dir():
        append_data_dir(str(data_path))
# End configure_grids function


def get_crs_from_source(source: Union[CRS, 'FeatureClass', SpatialReferenceSystem]) -> CRS:
    """
    Returns a CRS object from a Feature Class, Spatial Reference System,
    or CRS object.
    """
    if isinstance(source, CRS):
        return source
    if isinstance(source, SpatialReferenceSystem):
        srs = source
    else:
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


def srs_from_crs(crs: CRS) -> SpatialReferenceSystem:
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
# End srs_from_crs function


def crs_from_srs(srs: SpatialReferenceSystem) -> CRS:
    """
    Returns a CRS object from a Spatial Reference System object.  Simple
    alias function for get_crs_from_source.
    """
    return get_crs_from_source(source=srs)
# End crs_from_srs function


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


def check_same_crs(a: Union[CRS, 'FeatureClass'],
                   b: Union[CRS, 'FeatureClass']) -> None:
    """
    Check Feature Classes have the same CRS
    """
    if equals(get_crs_from_source(a), get_crs_from_source(b)):
        return
    raise CoordinateSystemDifferentError(
        'CRS for input feature classes must be the same')
# End check_same_crs function


def change_crs_dimension(source_crs: CRS, target_crs: CRS) -> tuple[CRS, CRS]:
    """
    Change CRS Dimensions to be internally consistent.
    """
    # NOTE if source is not compound but target is compound make target 2D
    #  since we really cannot convert Z values not knowing the source VCS
    if not source_crs.is_compound and target_crs.is_compound:
        return source_crs, target_crs.to_2d()
    # NOTE if target is not compound but source is compound make source 2D
    #  this is a lossy operation but the user is choosing it, do not convert Z
    elif source_crs.is_compound and not target_crs.is_compound:
        return source_crs.to_2d(), target_crs
    return source_crs, target_crs
# End change_crs_dimension function


def equals(source_crs: CRS, target_crs: CRS) -> bool:
    """
    Check if Coordinate Reference Systems are equal, account for compound crs
    adjusting to the same dimension.
    """
    source_crs, target_crs = change_crs_dimension(source_crs, target_crs)
    return source_crs.equals(target_crs, ignore_axis_order=True)
# End equals function


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


def get_crs_horizontal_component(crs: CRS) -> CRS:
    """
    Get CRS Horizontal Component
    """
    return _get_crs_component(crs, use_horizontal=True)
# End get_crs_horizontal_component function


def get_equidistant_projections(crs: CRS, coordinates: 'ndarray') \
        -> list[ProjectedCRS | None]:
    """
    Get Equidistant Projections using representative coordinates from
    geometries.  The coordinates should the same CRS as the input geometry
    and will be transformed to latitude / longitude if CRS is projected.
    """
    projections = []
    # noinspection PyTypeChecker
    geodetic_crs: CRS = crs.geodetic_crs
    coordinates = xy_to_dd(crs, coordinates=coordinates).round(-1)
    for lon, lat in coordinates:
        if not isfinite(lon) or not isfinite(lat):
            projections.append(None)
            continue
        projections.append(_equidistant_projection(
            geodetic_crs, lat=lat, lon=lon))
    return projections
# End get_equidistant_projections function


def get_equidistant_from_extent(source: 'FeatureClass') -> ProjectedCRS | None:
    """
    Get Equidistant Projection for an Extent, uses the centroid of the
    for the latitude and longitude values.  Rounding to the nearest 10 degree
    for latitude and longitude values when creating the equidistant projection.
    """
    crs = get_crs_from_source(source)
    extent = extent_from_index_or_geometry(source)
    if not isfinite(extent).all():
        return None
    digits = -1
    pt = get_geographic_extent_centroid(crs, extent=extent)
    lat, lon = round(pt.y, digits), round(pt.x, digits)
    # noinspection PyTypeChecker
    geodetic_crs: CRS = crs.geodetic_crs
    return _equidistant_projection(geodetic_crs, lat=lat, lon=lon)
# End get_equidistant_from_extent function


def get_geographic_extent_centroid(crs: CRS, extent: EXTENT) -> 'Point':
    """
    Get Geographic Centroid from an Extent
    """
    # noinspection PyTypeChecker
    poly: 'Polygon' = box(*extent)
    pt = poly.centroid
    if not crs.is_projected:
        return pt
    transformer = make_geodetic_transformer(crs)
    return transform(transformer.transform, pt)
# End get_geographic_extent_centroid function


def make_geodetic_transformer(crs: CRS) -> Transformer:
    """
    Make Geodetic Transformer
    """
    return Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
# End make_geodetic_transformer function


def xy_to_dd(crs: CRS, coordinates: 'ndarray') -> 'ndarray':
    """
    Transforms XY coordinates to Latitude / Longitude as needed
    """
    if not crs.is_projected:
        return coordinates
    transformer = make_geodetic_transformer(crs)
    xs, ys = transformer.transform(coordinates[:, 0], coordinates[:, 1])
    for i, values in enumerate((xs, ys)):
        coordinates[:, i] = values
    return coordinates
# End xy_to_lat_lon function


@lru_cache(maxsize=1000)
def _equidistant_projection(geodetic_crs: CRS, *, lat: float, lon: float) \
        -> ProjectedCRS:
    """
    Build an Azimuthal Equidistant Projection for the given latitude and
    longitude values.  Appears like we only need a projection for every
    10 x 10 degree block of latitude and longitude values.
    """
    conversion = AzimuthalEquidistantConversion(
        latitude_natural_origin=lat, longitude_natural_origin=lon)
    return ProjectedCRS(conversion=conversion, geodetic_crs=geodetic_crs)
# End _equidistant_projection function


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
