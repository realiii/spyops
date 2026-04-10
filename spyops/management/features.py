# -*- coding: utf-8 -*-
"""
Data Management for Features
"""


from typing import Callable, TYPE_CHECKING

from fudgeo import Field, SpatialReferenceSystem
from fudgeo import Table
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from fudgeo.enumeration import ShapeType
from fudgeo.util import get_extent
from pyproj import CRS

from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.crs.util import get_crs_from_source
from spyops.geometry.check import check_feature_class_geometry
from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.repair import repair_feature_class_geometry
from spyops.geometry.util import filter_features, to_shapely
from spyops.management.util import _build_lines_factory
from spyops.query.management.features import (
    QueryAddXYCoordinates, QueryCalculateGeometryAttributes, QueryCheckGeometry,
    QueryCopyFeatures, QueryFeatureEnvelopeToPolygon,
    QueryMultiPartToSinglePart, QueryRepairGeometry, QueryXYTableLine,
    QueryXYTablePoint)
from spyops.shared.keywords import (
    AREA_UNIT, CHECK_OPTIONS, COORDINATE_SYSTEM, END_X_FIELD, END_Y_FIELD,
    FIELD, GEOMETRY_ATTRIBUTE, LENGTH_UNIT, LINE_TYPE, M_FIELD, POINT_COUNT,
    SOURCE, START_X_FIELD, START_Y_FIELD, WEIGHT_OPTION, X_FIELD, Y_FIELD,
    Z_FIELD)
from spyops.shared.enumeration import (
    DEFAULT_GEOM_CHECKS, GeometryAttribute, GeometryCheck, LineTypeOption,
    WeightOption)
from spyops.shared.field import GEOM_TYPE_MULTI
from spyops.shared.hint import ELEMENT, XY_TOL
from spyops.shared.records import (
    extend_records, insert_many, select_and_transform_features)
from spyops.validation import (
    validate_coordinate_system, validate_element, validate_int_flag_enumeration,
    validate_range, validate_source_element, validate_source_numeric_field,
    validate_str_enumeration, validate_feature_class,
    validate_geometry_attribute, validate_overwrite_source, validate_result,
    validate_source_feature_class, validate_target_feature_class,
    validate_target_table, validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = [
    'add_xy_coordinates', 'calculate_geometry_attributes', 'check_geometry',
    'copy_features', 'delete_features', 'explode', 'multipart_to_singlepart',
    'repair_geometry', 'xy_table_to_point', 'xy_table_to_line', 'xy_to_line',
    'feature_envelope_to_polygon']


@validate_result()
@validate_feature_class(SOURCE, geometry_types=GEOM_TYPE_MULTI)
@validate_target_feature_class()
@validate_overwrite_source()
def multipart_to_singlepart(source: 'FeatureClass',
                            target: 'FeatureClass') -> 'FeatureClass':
    """
    MultiPart to Single Part

    Generates a feature class with single-part geometries by splitting
    multipart input features.  A column named ORIG_FID is added to the output
    feature class to track the original feature identifier.
    """
    parts = []
    records = []
    query = QueryMultiPartToSinglePart(source, target=target)
    insert_sql = query.insert
    config = query.geometry_config
    transformer = query.source_transformer
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            for geom, *attrs in features:
                parts.extend([(part, *attrs) for part in geom])
            insert_many(config, executor=executor, transformer=transformer,
                        insert_sql=insert_sql, features=parts, records=records)
            parts.clear()
    return query.target
# End multipart_to_singlepart function


@validate_result()
@validate_element(SOURCE, has_content=False)
def delete_features(source: ELEMENT, *, where_clause: str = '') -> ELEMENT:
    """
    Delete rows from a Table or Feature Class

    Deletes rows from a table or feature class using a where clause (optional).
    """
    source.delete(where_clause=where_clause)
    return source
# End delete_features function


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_overwrite_source()
def copy_features(source: 'FeatureClass', target: 'FeatureClass', *,
                  where_clause: str = '') -> 'FeatureClass':
    """
    Copy Features

    Copies features from one feature class to another.  Optionally, select
    features using a where clause.
    """
    query = QueryCopyFeatures(source, target=target, where_clause=where_clause)
    return select_and_transform_features(query)
# End copy_features function


@validate_result()
@validate_source_feature_class()
@validate_str_enumeration(WEIGHT_OPTION, WeightOption)
def add_xy_coordinates(source: 'FeatureClass', *,
                       weight_option: WeightOption = WeightOption.TWO_D) \
        -> 'FeatureClass':
    """
    Add XY Coordinates

    Adds POINT_X and POINT_Y fields to a feature class.  Adds a POINT_Z field
    when the feature class is Z enabled and POINT_M field when the feature
    class is M enabled.  If the feature class already contains
    these fields, then the values in these fields will be updated.

    XY and Z values will be in the coordinate system of the feature class or
    the output coordinate system when set.
    """
    with QueryAddXYCoordinates(source, weight_option) as query:
        query_insert = query.insert
        getter = query.centroid_getter
        transformer = query.source_transformer
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=transformer)
                records = [(i, *c) for (_, i), c in
                           zip(features, getter(geometries))]
                cin.executemany(query_insert, records)
            cin.execute(query.update)
    return query.target
# End add_xy_coordinates function


@validate_result()
@validate_source_feature_class()
@validate_source_numeric_field(FIELD)
@validate_str_enumeration(GEOMETRY_ATTRIBUTE, GeometryAttribute)
@validate_str_enumeration(WEIGHT_OPTION, WeightOption)
@validate_str_enumeration(LENGTH_UNIT, LengthUnit)
@validate_str_enumeration(AREA_UNIT, AreaUnit)
@validate_geometry_attribute()
def calculate_geometry_attributes(source: 'FeatureClass', field: Field | str,
                                  geometry_attribute: GeometryAttribute, *,
                                  weight_option: WeightOption = WeightOption.TWO_D,
                                  length_unit: LengthUnit = LengthUnit.METERS,
                                  area_unit: AreaUnit = AreaUnit.SQUARE_METERS) \
        -> 'FeatureClass':
    """
    Calculate Geometry Attributes

    Calculates geometry attributes for a feature class.  Options vary based on
    the geometry type and dimensionality of the geometry, that is, does the
    geometry have Z and / or M values.  Geometry attributes will be
    calculated using the feature class's coordinate reference system
    or the output coordinate system when set.

    Point
    -----
    POINT_X -- x-coordinate
    POINT_Y -- y-coordinate
    POINT_Z -- z-coordinate
    POINT_M -- m-value

    MultiPoint
    ----------
    CENTROID_X -- centroid x-coordinate
    CENTROID_Y -- centroid y-coordinate
    CENTROID_Z -- centroid z-coordinate
    CENTROID_M -- centroid m-value
    EXTENT_MIN_X -- minimum x-coordinate
    EXTENT_MIN_Y -- minimum y-coordinate
    EXTENT_MIN_Z -- minimum z-coordinate
    EXTENT_MIN_M -- minimum m-value
    EXTENT_MAX_X -- maximum x-coordinate
    EXTENT_MAX_Y -- maximum y-coordinate
    EXTENT_MAX_Z -- maximum z-coordinate
    EXTENT_MAX_M -- maximum m-value
    PART_COUNT -- number of parts
    POINT_COUNT -- number of points

    LineString and MultiLineString
    ------------------------------
    CENTROID_X -- centroid x-coordinate
    CENTROID_Y -- centroid y-coordinate
    CENTROID_Z -- centroid z-coordinate
    CENTROID_M -- centroid m-value
    EXTENT_MIN_X -- minimum x-coordinate
    EXTENT_MIN_Y -- minimum y-coordinate
    EXTENT_MIN_Z -- minimum z-coordinate
    EXTENT_MIN_M -- minimum m-value
    EXTENT_MAX_X -- maximum x-coordinate
    EXTENT_MAX_Y -- maximum y-coordinate
    EXTENT_MAX_Z -- maximum z-coordinate
    EXTENT_MAX_M -- maximum m-value
    INSIDE_X -- x-coordinate of a central point on the line
    INSIDE_Y -- y-coordinate of a central point on the line
    LENGTH -- length
    LENGTH_GEODESIC -- geodesic length
    LINE_AZIMUTH -- line azimuth
    LINE_START_X -- start point x-coordinate
    LINE_START_Y -- start point y-coordinate
    LINE_START_Z -- start point z-coordinate
    LINE_START_M -- start point m-value
    LINE_END_X -- end point x-coordinate
    LINE_END_Y -- end point y-coordinate
    LINE_END_Z -- end point z-coordinate
    LINE_END_M -- end point m-value
    PART_COUNT -- number of parts
    POINT_COUNT -- number of points

    Polygon and MultiPolygon
    ------------------------
    AREA -- area
    AREA_GEODESIC -- geodesic area
    CENTROID_X -- centroid x-coordinate
    CENTROID_Y -- centroid y-coordinate
    CENTROID_Z -- centroid z-coordinate
    CENTROID_M -- centroid m-value
    EXTENT_MIN_X -- minimum x-coordinate
    EXTENT_MIN_Y -- minimum y-coordinate
    EXTENT_MIN_Z -- minimum z-coordinate
    EXTENT_MIN_M -- minimum m-value
    EXTENT_MAX_X -- maximum x-coordinate
    EXTENT_MAX_Y -- maximum y-coordinate
    EXTENT_MAX_Z -- maximum z-coordinate
    EXTENT_MAX_M -- maximum m-value
    INSIDE_X -- x-coordinate of a central point inside the polygon
    INSIDE_Y -- y-coordinate of a central point inside the polygon
    PERIMETER -- perimeter (exterior and interior)
    PERIMETER_GEODESIC -- geodesic perimeter (exterior and interior)
    PART_COUNT -- number of parts
    POINT_COUNT -- number of points
    HOLE_COUNT -- number of holes
    """
    field: Field
    with QueryCalculateGeometryAttributes(
            source, field=field, geometry_attribute=geometry_attribute,
            weight_option=weight_option, length_unit=length_unit,
            area_unit=area_unit) as query:
        query_insert = query.insert
        item_getter = query.item_getter
        attr_getter = query.attribute_getter
        transformer = query.source_transformer
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=transformer)
                records = [(i, item_getter(values)) for (_, i), values in
                           zip(features, attr_getter(geometries))]
                cin.executemany(query_insert, records)
            cin.execute(query.update)
    return query.target
# End calculate_geometry_attributes function


@validate_result()
@validate_source_feature_class()
@validate_target_table()
@validate_int_flag_enumeration(CHECK_OPTIONS, GeometryCheck)
@validate_xy_tolerance()
@validate_overwrite_source()
def check_geometry(source: 'FeatureClass', target: 'Table',
                   check_options: GeometryCheck = DEFAULT_GEOM_CHECKS, *,
                   xy_tolerance: XY_TOL = None) -> 'Table':
    """
    Check Geometry

    Check geometries in a feature class for errors.  The checks performed vary
    based on the geometry type and dimensionality of the geometry, that is,
    whether the geometry is a point, line, or polygon, and whether it has Z
    values and M values.  The results are written to a table.

    Multiple checks are specified an OR operation, for example, to check
    for empty geometries, empty points, and nan Z values use:

    >>> check_geometry(source, target, check_options=(
    ...     GeometryCheck.EMPTY | GeometryCheck.EMPTY_POINT |
    ...     GeometryCheck.NAN_Z))

    It is ok to specify a check option that does not apply to the geometry,
    it will be ignored.  The following checks are available:

    * EXTENT: checks if the feature class extent is set and if it is, then this
      is compared to the geometry extent

    * EMPTY: checks if the geometry is empty
    * EMPTY_PART: checks if any part of the geometry is empty, this is applied
      to multipart geometries only
    * EMPTY_POINT: checks if any point in the geometry is empty
    * POINT_COUNT: checks if the number of points in the geometry is valid,
      for lines this is 2 and for polygons this is 3

    * EMPTY_RING: checks if any ring in a polygon geometry is empty
    * ORIENTATION: checks if the polygon geometry has a valid orientation
    * UNCLOSED: checks if the polygon geometry is closed
    * SELF_INTERSECTION: checks if the polygon geometry has self-intersections
    * OUTSIDE_RING: checks if the polygon geometry has rings that are
      outside the exterior ring
    * OVERLAP_RING: checks if the polygon geometry has rings that overlap

    * NAN_Z: checks if the geometry has any Z values that are NaN
    * NAN_M: checks if the geometry has any M values that are NaN
    * REPEATED_XY: checks if the geometry has any repeated XY coordinates, the
      xy tolerance is used to determine if two points are considered the same,
      if not set, then the xy tolerance is set 1e-8
    * REPEATED_M: checks if the geometry has any repeated M values
    * MISMATCH_Z: checks if the geometry has different Z values for the same XY
    * MISMATCH_M: checks if the geometry has different M values for the same XY

    The default checks are: EXTENT, EMPTY, EMPTY_PART, EMPTY_RING, EMPTY_POINT,
    NAN_Z, NAN_M, REPEATED_XY, REPEATED_M, MISMATCH_Z, and MISMATCH_M.
    """
    query = QueryCheckGeometry(source, target=target, xy_tolerance=xy_tolerance)
    records = check_feature_class_geometry(
        query.source, options=check_options, grid_size=query.grid_size)
    with query.target.geopackage.connection as cout:
        cout.executemany(query.insert, records)
    return query.target
# End check_geometry function


@validate_result()
@validate_source_feature_class()
def repair_geometry(source: 'FeatureClass', drop_empty: bool = False) \
        -> 'FeatureClass':
    """
    Repair Geometry

    Repairs geometries in a feature class.  The repairs perform very based
    on the geometry type.  The repairs performed:

    * EMPTY: drops empty features (if drop_empty=True), sets to empty otherwise
    * EMPTY_POINT: removes empty points (i.e., XY values are NaN), removing
      points may cause emptiness in rings, parts, and / or geometries
    * EMPTY_PART: removes empty parts from multipart geometries
    * EMPTY_RING: checks if any ring in a polygon geometry is empty
    * POINT_COUNT: applies to lines and polygons, lines must have at least 2
      points and polygons 3 points, fixes are attempted, but bad point count
      will likely result in an empty geometry.
    * UNCLOSED: ensures polygon rings are closed
    * ORIENTATION: corrects the orientation for rings in a polygon
    * SELF_INTERSECTION: fixes self-intersections as best as possible, this
      is best handled as a manual edit
    * OUTSIDE_RING: fixes this configuration as best as possible, this
      is best handled as a manual edit
    * OVERLAP_RING: fixes overlaps as best as possible, this is best handled
      as a manual edit
    * EXTENT: updates the feature class extent to match the geometry extent
    """
    with QueryRepairGeometry(source) as query:
        with (query.source.geopackage.connection as cin,
              ExecuteMany(connection=cin, table=query.target) as executor):
            updates, identifiers = repair_feature_class_geometry(
                query.source, drop_empty=drop_empty)
            if drop_empty:
                cin.executemany(query.insert_identifiers, identifiers)
                cin.execute(query.drop_empty)
                cin.execute(query.truncate)
            executor(sql=query.insert, data=updates)
            cin.execute(query.update)
            query.source.extent = get_extent(query.source)
    return query.source
# End repair_geometry function


@validate_result()
@validate_source_element()
@validate_target_feature_class()
@validate_coordinate_system(COORDINATE_SYSTEM)
@validate_source_numeric_field(X_FIELD)
@validate_source_numeric_field(Y_FIELD)
@validate_source_numeric_field(Z_FIELD, is_optional=True)
@validate_source_numeric_field(M_FIELD, is_optional=True)
@validate_overwrite_source()
def xy_table_to_point(source: ELEMENT, target: 'FeatureClass',
                      coordinate_system: CRS | SpatialReferenceSystem, *,
                      x_field: Field | str, y_field: Field | str,
                      z_field: Field | str | None = None,
                      m_field: Field | str | None = None) -> 'FeatureClass':
    """
    XY Table to Point

    Converts a table with XY coordinates into a point feature class.  Optionally
    allows for Z and / or M values to be added to each point.  The input fields
    for XY (and Z / M) must be numeric, fields from the input table will be
    added to the output feature class.

    The output feature class will be in the specified coordinate reference
    system or will be transformed to from the specified coordinate reference
    into the analysis settings output coordinate reference system.
    """
    records = []
    fields = x_field, y_field, z_field, m_field
    # noinspection PyTypeChecker
    query = QueryXYTablePoint(source, target=target, fields=fields,
                              coordinate_system=coordinate_system)
    cls = query.point_class
    insert_sql = query.insert
    getter = query.item_getter
    extent = query.filter_extent
    config = query.geometry_config
    transformer = query.source_transformer
    srs_id = query.target.spatial_reference_system.srs_id
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while rows := cursor.fetchmany(FETCH_SIZE):
            features = [(cls.from_tuple(getter(row), srs_id=srs_id), *row)
                        for row in rows]
            if not (features := filter_features(features)):
                continue
            insert_many(config, executor=executor, transformer=transformer,
                        insert_sql=insert_sql, features=features,
                        records=records, extent=extent)
    return query.target
# End xy_table_to_point function


@validate_result()
@validate_source_element()
@validate_target_feature_class()
@validate_coordinate_system(COORDINATE_SYSTEM)
@validate_source_numeric_field(START_X_FIELD)
@validate_source_numeric_field(START_Y_FIELD)
@validate_source_numeric_field(END_X_FIELD)
@validate_source_numeric_field(END_Y_FIELD)
@validate_str_enumeration(LINE_TYPE, LineTypeOption)
@validate_range(POINT_COUNT, default=9, max_value=1000, type_=int)
@validate_overwrite_source()
def xy_to_line(source: ELEMENT, target: 'FeatureClass',
               coordinate_system: CRS | SpatialReferenceSystem, *,
               start_x_field: Field | str, start_y_field: Field | str,
               end_x_field: Field | str, end_y_field: Field | str,
               line_type: LineTypeOption = LineTypeOption.GEODESIC,
               point_count: int = 9) -> 'FeatureClass':
    """
    XY to Line

    Converts a table with Start XY and End XY coordinates into a line feature
    class.  The input fields for XY must be numeric, fields from the input
    table will be added to the output feature class.  The output feature
    class will be in the specified coordinate reference system.

    The line type option determines the type of line that is created.  The
    point count specifies the number of additional points to be created
    along the line in addition to the start and end points.
    """
    records = []
    fields: tuple[Field, Field, Field, Field]
    # noinspection PyTypeChecker
    fields = start_x_field, start_y_field, end_x_field, end_y_field
    query = QueryXYTableLine(source, target=target, fields=fields,
                             coordinate_system=coordinate_system)
    insert_sql = query.insert
    getter = query.item_getter
    config = query.geometry_config
    srs_id = query.target.spatial_reference_system.srs_id
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while rows := cursor.fetchmany(FETCH_SIZE):
            lines = _build_lines_factory(
                coords=[getter(row) for row in rows],
                crs=get_crs_from_source(coordinate_system),
                srs_id=srs_id, line_type=line_type, point_count=point_count)
            features = [(line, *row) for line, row in zip(lines, rows)]
            if not (features := filter_features(features)):
                continue
            insert_many(config, executor=executor, transformer=None,
                        insert_sql=insert_sql, features=features,
                        records=records)
    return query.target
# End xy_to_line function


@validate_result()
@validate_feature_class(SOURCE, geometry_types=(
        ShapeType.multi_point, ShapeType.linestring, ShapeType.multi_linestring,
        ShapeType.polygon, ShapeType.multi_polygon))
@validate_target_feature_class()
@validate_overwrite_source()
def feature_envelope_to_polygon(source: 'FeatureClass', target: 'FeatureClass',
                                as_multi_part: bool = False) -> 'FeatureClass':
    """
    Feature Envelope to Polygon

    Create a polygon feature class where each polygon represents the extent of
    the feature (or the parts) in the source feature class coordinate reference
    system or in the Output Coordinate System via Settings.

    Use as_multi_part=True to create a MultiPolygon feature class where each
    polygon represents the extent of the Parts of the input geometries.
    """
    records = []
    query = QueryFeatureEnvelopeToPolygon(
        source, target=target, as_multi_part=as_multi_part)
    insert_sql = query.insert
    config = query.geometry_config
    extent_getter = query.extent_getter
    transformer = query.source_transformer
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geometries = to_shapely(
                features, transformer=transformer,
                option=DimensionOption.TWO_D)
            geometries = extent_getter(geometries)
            results = [(g, attrs) for g, (_, *attrs) in
                       zip(geometries, features)]
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End feature_envelope_to_polygon function


explode: Callable[['FeatureClass', 'FeatureClass'], 'FeatureClass'] = multipart_to_singlepart
xy_table_to_line: Callable[[ELEMENT, 'FeatureClass', CRS | SpatialReferenceSystem,
                            Field | str, Field | str, Field | str, Field | str,
                            LineTypeOption, int], 'FeatureClass'] = xy_to_line


if __name__ == '__main__':  # pragma: no cover
    pass
