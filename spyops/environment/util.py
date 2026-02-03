# -*- coding: utf-8 -*-
"""
Utility Functions
"""


from math import hypot
from typing import Optional, TYPE_CHECKING

from numpy import isnan
from pyproj import Transformer
from shapely.creation import box
from shapely.ops import transform

from spyops.crs.unit import get_unit_conversion_factor, get_unit_name
from spyops.crs.util import crs_from_srs, equals, get_crs_from_source
from spyops.environment.enumeration import Setting
from spyops.geometry.extent import extent_from_feature_class
from spyops.shared.constant import DEGREE, EMPTY, METRE, SPACE, UNDERSCORE
from spyops.shared.hint import GRID_SIZE, XY_TOL


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, SpatialReferenceSystem
    from pyproj import CRS


def as_title(setting: Setting | str | None) -> str:
    """
    Change a setting enumeration value to a title text for exceptions
    """
    if setting is None:
        return EMPTY
    if setting == Setting.XY_TOLERANCE:
        return 'XY Tolerance'
    return str(setting).replace(UNDERSCORE, SPACE).title()
# End as_title function


def _scale_factor(feature_class: 'FeatureClass') -> float:
    """
    Scale Factor approximation for 1 metre of XY Tolerance in Decimal Degrees,
    if the CRS is geographic or the extent is invalid then return 1, that is,
    no scaling will occur.
    """
    extent = extent_from_feature_class(feature_class)
    if isnan(extent).any():
        return 1
    crs = get_crs_from_source(feature_class)
    pt = box(*extent, ccw=False).centroid
    if crs.is_projected:
        transformer = Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
        pt = transform(transformer.transform, pt)
    geod = crs.geodetic_crs.get_geod()
    center_x, center_y = pt.x, pt.y
    x, y, _ = geod.fwd(lons=center_x, lats=center_y, az=0, dist=1)
    return hypot(center_x - x, center_y - y)
# End _scale_factor function


def get_grid_size(source: 'FeatureClass', xy_tolerance: XY_TOL,
                  target_srs: Optional['SpatialReferenceSystem']) -> GRID_SIZE:
    """
    Calculate Grid Size based on Source Spatial Reference, XY Tolerance, and
    the target spatial reference system (which may be defined by the output
    coordinate system of the analysis environment or by the source spatial
    reference system).
    """
    if not xy_tolerance or not target_srs:
        return xy_tolerance
    crs = crs_from_srs(target_srs)
    source_crs = get_crs_from_source(source)
    if equals(source_crs, crs):
        return xy_tolerance
    crs_unit_name = get_unit_name(crs)
    source_crs_unit_name = get_unit_name(source_crs)
    if crs_unit_name == source_crs_unit_name:
        return xy_tolerance
    if crs_unit_name == DEGREE:
        crs_unit_name = METRE
        xy_tolerance *= _scale_factor(source)
    elif source_crs_unit_name == DEGREE:
        source_crs_unit_name = METRE
        xy_tolerance /= _scale_factor(source)
    return xy_tolerance * get_unit_conversion_factor(
        from_name=source_crs_unit_name, to_name=crs_unit_name)
# End get_grid_size function


def get_geographic_transformation(source_crs: 'CRS', target_crs: 'CRS',
                                  transformations: list[Transformer]) \
        -> Optional[Transformer]:
    """
    Get Geographic Transformation from Analysis Settings
    """
    if not transformations or equals(source_crs, target_crs):
        return None
    for transformer in transformations:
        if (equals(transformer.source_crs, source_crs) and
                equals(transformer.target_crs, target_crs)):
            return transformer
    return None
# End get_geographic_transformation function


if __name__ == '__main__':  # pragma: no cover
    pass
