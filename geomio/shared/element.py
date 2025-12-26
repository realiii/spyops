# -*- coding: utf-8 -*-
"""
Feature Class Functionality
"""


from sqlite3 import OperationalError

from fudgeo import FeatureClass, SpatialReferenceSystem

from geomio.crs.util import validate_srs
from geomio.shared.exception import OperationsError
from geomio.shared.hint import ELEMENT, FIELDS, GPKG
from geomio.shared.setting import ANALYSIS_SETTINGS


def copy_feature_class(source: FeatureClass, target: FeatureClass, *,
                       where_clause: str = '') -> FeatureClass:
    """
    Copy Feature Class, accounting for potential Spatial Reference System
    differences across GeoPackages and ensuring the target has a spatial index.
    """
    overwrite = ANALYSIS_SETTINGS.overwrite
    geopackage = target.geopackage
    srs = validate_srs(geopackage, srs=source.spatial_reference_system)
    target = source.copy(
        name=target.name, geopackage=geopackage, where_clause=where_clause,
        overwrite=overwrite, srs=srs)
    target.add_spatial_index()
    return target
# End copy_feature_class function


def create_feature_class(geopackage: GPKG, name: str, shape_type: str,
                         srs: SpatialReferenceSystem, *, fields: FIELDS = (),
                         z_enabled: bool = False, m_enabled: bool = False,
                         description: str = '') -> FeatureClass:
    """
    Create Feature Class, a light wrapper around the create method of
    FeatureClass with some additional logic for Spatial Reference handling and
    ensuring spatial indexes are present.
    """
    overwrite = ANALYSIS_SETTINGS.overwrite
    srs = validate_srs(geopackage, srs=srs)
    return FeatureClass.create(
        geopackage=geopackage, name=name, shape_type=shape_type, srs=srs,
        z_enabled=z_enabled, m_enabled=m_enabled, fields=fields,
        description=description, overwrite=overwrite, spatial_index=True)
# End create_feature_class function


def copy_element(source: ELEMENT, target: ELEMENT, *,
                 where_clause: str = '') -> ELEMENT:
    """
    Copy Element, wrapper for Feature Class or Table
    """
    try:
        if isinstance(source, FeatureClass):
            element = copy_feature_class(
                source=source, target=target, where_clause=where_clause)
        else:
            overwrite = ANALYSIS_SETTINGS.overwrite
            element = source.copy(
                name=target.name, geopackage=target.geopackage,
                where_clause=where_clause, overwrite=overwrite)
    except (OperationalError, ValueError) as err:  # pragma: no cover
        raise OperationsError(err)
    return element
# End copy_element function


if __name__ == '__main__':  # pragma: no cover
    pass
