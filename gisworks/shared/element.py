# -*- coding: utf-8 -*-
"""
Feature Class and some Table Functionality
"""


from sqlite3 import OperationalError

from fudgeo import FeatureClass, SpatialReferenceSystem
from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.context import ExecuteMany

from gisworks.crs.util import validate_srs
from gisworks.environment import ANALYSIS_SETTINGS
from gisworks.environment.core import zm_config
from gisworks.geometry.config import geometry_config
from gisworks.geometry.util import filter_features, to_shapely
from gisworks.shared.constant import QUESTION
from gisworks.shared.exception import OperationsError
from gisworks.shared.field import get_geometry_column_name, validate_fields
from gisworks.shared.hint import ELEMENT, FIELDS, GPKG
from gisworks.shared.util import extend_records


def copy_feature_class(source: FeatureClass, target: FeatureClass, *,
                       where_clause: str = '') -> FeatureClass:
    """
    Copy Feature Class, accounting for potential Spatial Reference System
    differences across GeoPackages and ensuring the target has a spatial index.
    """
    geopackage = target.geopackage
    srs = validate_srs(geopackage, srs=source.spatial_reference_system)
    if not zm_config(has_z=source.has_z, has_m=source.has_m).is_different:
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
            z_enabled=source.has_z, m_enabled=source.has_m)
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
        records = []
        config = geometry_config(target, cast_geom=True)
        with (target.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=target) as executor):
            cursor = source.select(fields=fields, where_clause=where_clause)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                geometries = to_shapely(features)
                results = [(g, attrs) for g, (_, *attrs)
                           in zip(geometries, features)]
                extend_records(results, records=records, config=config)
                executor(sql=insert_sql, data=records)
                records.clear()
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
    srs = validate_srs(geopackage, srs=srs)
    zm = zm_config(has_z=z_enabled, has_m=m_enabled)
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
