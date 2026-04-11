# -*- coding: utf-8 -*-
"""
Feature Class and some Table Functionality
"""


from sqlite3 import OperationalError

from fudgeo import FeatureClass, SpatialReferenceSystem
from fudgeo.constant import COMMA_SPACE, SHAPE
from fudgeo.context import ExecuteMany
from pyproj import CRS

from spyops.crs.transform import (
    get_transform_best_guess, make_transformer_function)
from spyops.crs.util import crs_from_srs, srs_from_crs, validate_srs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.core import HasZM, ZMConfig, zm_config
from spyops.environment.util import get_geographic_transformation
from spyops.geometry.config import geometry_config
from spyops.shared.constant import QUESTION
from spyops.shared.exception import OperationsError
from spyops.shared.field import get_geometry_column_name, validate_fields
from spyops.shared.hint import ELEMENT, FIELDS, GPKG
from spyops.shared.records import bulk_insert


def copy_feature_class(source: FeatureClass, target: FeatureClass, *,
                       where_clause: str = '', zm: ZMConfig) -> FeatureClass:
    """
    Copy Feature Class, accounting for potential Spatial Reference System
    differences across GeoPackages and ensuring the target has a spatial index.
    """
    crs = ANALYSIS_SETTINGS.output_coordinate_system
    if not isinstance(crs, CRS):
        srs = source.spatial_reference_system
        transformer = None
    else:
        srs = srs_from_crs(crs)
        source_crs = crs_from_srs(source.spatial_reference_system)
        if not (transformer := get_geographic_transformation(
                source_crs=source_crs, target_crs=crs,
                transformations=ANALYSIS_SETTINGS.geographic_transformations)):
            transformer = get_transform_best_guess(source_crs, crs)
        transformer = make_transformer_function(
            source.shape_type, has_z=source.has_z, has_m=source.has_m,
            transformer=transformer)
    geopackage = target.geopackage
    # noinspection PyTypeChecker
    srs = validate_srs(geopackage, srs=srs)
    # NOTE simple copy if no change in ZM and no change in CRS
    if not zm.is_different and not transformer:
        target = source.copy(
            name=target.name, geopackage=geopackage, where_clause=where_clause,
            overwrite=ANALYSIS_SETTINGS.overwrite, srs=srs)
        target.add_spatial_index()
    else:
        fields = validate_fields(source, fields=source.fields)
        # NOTE send in source has_z and has_m, rely on handling of zm in the
        #  create_feature_class function
        # noinspection PyTypeChecker
        target = create_feature_class(
            geopackage, name=target.name, shape_type=source.shape_type, srs=srs,
            fields=fields, description=target.description,
            geom_name=source.geometry_column_name,
            z_enabled=zm.z_enabled, m_enabled=zm.m_enabled)
        geom_name = get_geometry_column_name(target)
        if fields:
            field_names = COMMA_SPACE.join(f.escaped_name for f in fields)
            field_names = f'{geom_name}{COMMA_SPACE}{field_names}'
        else:
            field_names = geom_name
        params = COMMA_SPACE.join(QUESTION * (len(fields) + 1))
        insert_sql = f"""
            INSERT INTO {target.escaped_name}({field_names}) 
            VALUES ({params})
        """
        geom_config = geometry_config(target, cast_geom=True)
        with (target.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=target) as executor):
            cursor = source.select(fields=fields, where_clause=where_clause)
            bulk_insert(cursor, config=geom_config, executor=executor,
                        insert_sql=insert_sql, transformer=transformer)
    return target
# End copy_feature_class function


def create_feature_class(geopackage: GPKG, name: str, shape_type: str,
                         srs: SpatialReferenceSystem, *, fields: FIELDS = (),
                         z_enabled: bool = False, m_enabled: bool = False,
                         description: str = '', geom_name: str = SHAPE,
                         override_zm: bool = False) -> FeatureClass:
    """
    Create Feature Class, a light wrapper around the create method of
    FeatureClass with some additional logic for Spatial Reference handling and
    ensuring spatial indexes are present.
    """
    srs = validate_srs(geopackage, srs=srs)
    if override_zm:
        zm = ZMConfig(
            is_different=False, z_enabled=z_enabled, m_enabled=m_enabled)
    else:
        zm = zm_config(HasZM(has_z=z_enabled, has_m=m_enabled))
    # noinspection PyArgumentEqualDefault
    return FeatureClass.create(
        geopackage=geopackage, name=name, shape_type=shape_type, srs=srs,
        z_enabled=zm.z_enabled, m_enabled=zm.m_enabled, fields=fields,
        description=description, overwrite=ANALYSIS_SETTINGS.overwrite,
        spatial_index=True, geom_name=geom_name)
# End create_feature_class function


def copy_element(source: ELEMENT, target: ELEMENT, *,
                 where_clause: str = '') -> ELEMENT:
    """
    Copy Element, wrapper for Feature Class or Table
    """
    try:
        if isinstance(source, FeatureClass):
            zm = zm_config(source)
            # noinspection PyTypeChecker
            element = copy_feature_class(
                source=source, target=target, where_clause=where_clause, zm=zm)
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
