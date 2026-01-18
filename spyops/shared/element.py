# -*- coding: utf-8 -*-
"""
Feature Class and some Table Functionality
"""


from sqlite3 import OperationalError

from fudgeo import FeatureClass, SpatialReferenceSystem
from fudgeo.constant import COMMA_SPACE
from fudgeo.context import ExecuteMany

from spyops.crs.util import validate_srs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.core import HasZM, ZMConfig, zm_config
from spyops.geometry.config import geometry_config
from spyops.shared.constant import QUESTION
from spyops.shared.exception import OperationsError
from spyops.shared.field import get_geometry_column_name, validate_fields
from spyops.shared.hint import ELEMENT, FIELDS, GPKG
from spyops.shared.records import bulk_insert


def copy_feature_class(source: FeatureClass, target: FeatureClass, *,
                       where_clause: str = '', config: ZMConfig) -> FeatureClass:
    """
    Copy Feature Class, accounting for potential Spatial Reference System
    differences across GeoPackages and ensuring the target has a spatial index.
    """
    geopackage = target.geopackage
    srs = validate_srs(geopackage, srs=source.spatial_reference_system)
    if not config.is_different:
        target = source.copy(
            name=target.name, geopackage=geopackage, where_clause=where_clause,
            overwrite=ANALYSIS_SETTINGS.overwrite, srs=srs)
        target.add_spatial_index()
    else:
        fields = validate_fields(source, fields=source.fields)
        # NOTE send in source has_z and has_m, rely on handling of zm in the
        #  create_feature_class function
        target = create_feature_class(
            geopackage, name=target.name, shape_type=source.shape_type, srs=srs,
            fields=fields, description=target.description,
            z_enabled=config.z_enabled, m_enabled=config.m_enabled)
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
        config = geometry_config(target, cast_geom=True)
        with (target.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=target) as executor):
            cursor = source.select(fields=fields, where_clause=where_clause)
            bulk_insert(cursor, config=config, executor=executor,
                        insert_sql=insert_sql)
    return target
# End copy_feature_class function


def create_feature_class(geopackage: GPKG, name: str, shape_type: str,
                         srs: SpatialReferenceSystem, *, fields: FIELDS = (),
                         z_enabled: bool = False, m_enabled: bool = False,
                         description: str = '', override_zm: bool = False) -> FeatureClass:
    """
    Create Feature Class, a light wrapper around the create method of
    FeatureClass with some additional logic for Spatial Reference handling and
    ensuring spatial indexes are present.
    """
    srs = validate_srs(geopackage, srs=srs)
    if override_zm:
        zm = ZMConfig(is_different=False, z_enabled=z_enabled, m_enabled=m_enabled)
    else:
        zm = zm_config(HasZM(has_z=z_enabled, has_m=m_enabled))
    return FeatureClass.create(
        geopackage=geopackage, name=name, shape_type=shape_type, srs=srs,
        z_enabled=zm.z_enabled, m_enabled=zm.m_enabled, fields=fields,
        description=description, overwrite=ANALYSIS_SETTINGS.overwrite,
        spatial_index=True)
# End create_feature_class function


def copy_element(source: ELEMENT, target: ELEMENT, *,
                 where_clause: str = '') -> ELEMENT:
    """
    Copy Element, wrapper for Feature Class or Table
    """
    try:
        if isinstance(source, FeatureClass):
            config = zm_config(source)
            element = copy_feature_class(
                source=source, target=target, where_clause=where_clause,
                config=config)
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
