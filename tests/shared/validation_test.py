# -*- coding: utf-8 -*-
"""
Test Validation
"""


from pathlib import Path

from fudgeo import (
    Field, GeoPackage, MemoryGeoPackage, SpatialReferenceSystem, Table)
from fudgeo.enumeration import GeometryType, SQLFieldType
from pyproj import CRS
from pytest import mark, raises

from warnings import catch_warnings, simplefilter

from conftest import fresh_gpkg
from geomio.shared.exceptions import OperationsError, OperationsWarning
from geomio.shared.field import (
    GEOM_TYPE_LINES, GEOM_TYPE_POINTS,
    GEOM_TYPE_POLYGONS, REALS, TEXT_AND_NUMBERS)
from geomio.shared.util import element_names, make_unique_name
from geomio.shared.validation import (
    _check_output_empty, validate_element, validate_feature_class,
    validate_field, validate_geopackage, validate_same_crs, validate_table)


pytestmark = [mark.validation]


def test_check_output_empty(fresh_gpkg):
    """
    Test Check Output Empty
    """
    tbl = fresh_gpkg.create_table('tbl')
    with catch_warnings(record=True) as ws:
        simplefilter('always')
        _check_output_empty(tbl)
        assert len(ws) == 1
        w, = ws
        assert issubclass(w.category, OperationsWarning)
# End test_check_output_empty function


@mark.parametrize('exists, has_content', [
    (True, True),
    (True, False),
    (False, False),
    (False, True),
])
def test_validate_element_type(exists, has_content):
    """
    Test validate element type
    """
    @validate_element('element', exists=exists, has_content=has_content)
    def element_function(element):
        pass
    with raises(TypeError):
        element_function(element=Ellipsis)
# End test_validate_element_type function


@mark.parametrize('name, exists, has_content', [
    ('admin_a', True, True),
    ('admin_a', True, False),
    ('admin_a', False, False),
    ('admin_a', False, True),
    ('admin', True, True),
    ('admin', True, False),
    ('admin', False, False),
    ('admin', False, True),
    (None, True, True),
    (None, True, False),
    (None, False, False),
    (None, False, True),
    ('', True, True),
    ('', True, False),
    ('', False, False),
    ('', False, True),
])
def test_validate_element_data_type(world_features, world_tables, fresh_gpkg, name, exists, has_content):
    """
    Test validate element
    """
    @validate_element('element', exists=exists, has_content=has_content)
    def element_function(element):
        pass
    if name is None:
        names = element_names(fresh_gpkg)
        e = Table.create(fresh_gpkg, name=make_unique_name(str(name), names=names), fields=())
    elif not name:
        e = Table(fresh_gpkg, name='asdf')
    else:
        e = world_features.feature_classes.get(name, world_tables.tables.get(name))
    if name is None and exists and has_content:
        with raises(ValueError):
            element_function(element=e)
    elif name == '' and exists:
        with raises(ValueError):
            element_function(element=e)
    else:
        element_function(element=e)
# End test_validate_element_data_type function


@mark.parametrize('exists', [
    True, False
])
def test_validate_geopackage(fresh_gpkg, exists):
    """
    Test validate_geopackage
    """
    @validate_geopackage('gpkg', exists=exists)
    def geo_function(gpkg):
        pass
    with raises(TypeError):
        geo_function(None)
    if exists:
        with raises(ValueError):
            geo_function(GeoPackage(Path.home()))
    geo_function(fresh_gpkg)
    geo_function(MemoryGeoPackage())
# End test_validate_geopackage function


@mark.parametrize('name, geometry_types', [
    ('admin_a', ()),
    ('roads_l', ()),
    ('airports_p', ()),
    ('admin_a', GEOM_TYPE_POLYGONS),
    ('roads_l', GEOM_TYPE_LINES),
    ('airports_p', GEOM_TYPE_POINTS),
    ('admin_a', GeometryType.polygon),
    ('roads_l', GeometryType.linestring),
    ('airports_p', GeometryType.point),
    ('cities_p', GEOM_TYPE_POLYGONS),
])
def test_validate_feature_class_geometry(world_features, name, geometry_types):
    """
    Test validate feature class geometry
    """
    @validate_feature_class('feature_class', geometry_types=geometry_types)
    def fc_function(feature_class):
        pass
    fc = world_features.feature_classes[name]
    if name == 'cities_p':
        with raises(ValueError):
            fc_function(fc)
    else:
        fc_function(fc)
# End test_validate_feature_class_geometry function


@mark.parametrize('name, has_z, has_m', [
    ('admin_a', False, False),
    ('admin_a', True, False),
    ('admin_a', True, True),
    ('admin_a', False, True),
])
def test_validate_feature_class_zm(world_features, name, has_z, has_m):
    """
    Test validate feature class ZM
    """
    @validate_feature_class('feature_class', has_z=has_z, has_m=has_m)
    def fc_function(feature_class):
        pass
    fc = world_features.feature_classes[name]
    if has_z or has_m:
        with raises(ValueError):
            fc_function(fc)
    else:
        fc_function(fc)
# End test_validate_feature_class_zm function


@mark.parametrize('data_type, data_types, single, throws', [
    (SQLFieldType.float, (), True, False),
    (SQLFieldType.float, REALS, True, False),
    (SQLFieldType.float, TEXT_AND_NUMBERS, True, False),
    (SQLFieldType.text, TEXT_AND_NUMBERS, True, False),
    (SQLFieldType.text, REALS, True, True),
    (SQLFieldType.text, SQLFieldType.boolean, True, True),
    (SQLFieldType.float, (), False, False),
    (SQLFieldType.float, REALS, False, False),
    (SQLFieldType.float, TEXT_AND_NUMBERS, False, False),
    (SQLFieldType.text, TEXT_AND_NUMBERS, False, False),
    (SQLFieldType.text, REALS, False, True),
    (SQLFieldType.text, SQLFieldType.boolean, False, True),
])
def test_validate_field_data_type(data_type, data_types, single, throws):
    """
    Test validate field data type
    """
    @validate_field('field', data_types=data_types, single=single)
    def field_function(field):
        pass
    fld = Field('asdf', data_type=data_type)
    if throws:
        with raises(ValueError):
            field_function(fld)
    else:
        field_function(fld)
# End test_validate_field_data_type function


@mark.parametrize('fld, exists, throws', [
    (Field('NAME', data_type=SQLFieldType.text), True, False),
    (Field('name', data_type=SQLFieldType.text), True, False),
    (Field('asdf', data_type=SQLFieldType.text), True, True),
    (Field('NAME', data_type=SQLFieldType.text), False, False),
    (Field('name', data_type=SQLFieldType.text), False, False),
    (Field('asdf', data_type=SQLFieldType.text), False, True),
    ('asdf', True, True),
    ('NAME', True, False),
])
def test_validate_field_single_field(world_tables, fld, exists, throws):
    """
    Test validate field single field
    """
    @validate_table('table')
    @validate_field('field', element_name='table', single=True, exists=exists)
    def field_function(table, field):
        pass
    tbl = world_tables.tables['admin']
    if throws:
        with raises(ValueError):
            field_function(tbl, fld)
    else:
        field_function(tbl, fld)
# End test_validate_field_single_field function


@mark.parametrize('fld, exists, throws', [
    (Field('NAME', data_type=SQLFieldType.text), True, False),
    (Field('name', data_type=SQLFieldType.text), True, False),
    (Field('asdf', data_type=SQLFieldType.text), True, True),
    (Field('NAME', data_type=SQLFieldType.text), False, False),
    (Field('name', data_type=SQLFieldType.text), False, False),
    (Field('asdf', data_type=SQLFieldType.text), False, True),
    ('asdf', True, True),
    ('NAME', True, False),
])
def test_validate_field_multiple_fields(world_tables, fld, exists, throws):
    """
    Test validate field multiple fields
    """
    @validate_table('table')
    @validate_field('fields', element_name='table', single=False, exists=exists)
    def field_function(table, fields):
        pass
    tbl = world_tables.tables['admin']
    if throws:
        with raises(ValueError):
            field_function(tbl, fld)
    else:
        field_function(tbl, fld)
# End test_validate_field_multiple_fields function


def test_validate_same_crs(fresh_gpkg):
    """
    Test validate same crs
    """
    @validate_same_crs('a', 'b')
    def crs_function(a, b):
        pass
    srs_a = fresh_gpkg.spatial_references[4326]
    srs_b = SpatialReferenceSystem(name='NAD27', organization='EPSG', org_coord_sys_id=4267, definition=CRS(4267).to_wkt())
    fc_a = fresh_gpkg.create_feature_class('aaa', srs=srs_a)
    fc_b = fresh_gpkg.create_feature_class('bbb', srs=srs_b)
    with raises(OperationsError):
        crs_function(fc_a, fc_b)
# End test_validate_same_crs function


if __name__ == '__main__':  # pragma: no cover
    pass
