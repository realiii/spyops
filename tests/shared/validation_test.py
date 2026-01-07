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

from gisworks.geometry.validate import get_geometry_dimension
from gisworks.shared.enumeration import AttributeOption, OutputTypeOption, Setting
from gisworks.shared.exception import OperationsError, OperationsWarning
from gisworks.shared.field import (
    GEOM_TYPE_LINES, GEOM_TYPE_POINTS,
    GEOM_TYPE_POLYGONS, REALS, TEXT_AND_NUMBERS)
from gisworks.shared.setting import Swap
from gisworks.shared.util import element_names, make_unique_name
from gisworks.shared.validation import (
    _check_output, validate_element, validate_enumeration,
    validate_feature_class, validate_field, validate_geometry_dimension,
    validate_geopackage,
    validate_output_type, validate_result, validate_same_crs, validate_table,
    validate_xy_tolerance)


pytestmark = [mark.validation]


def test_check_output_empty(mem_gpkg):
    """
    Test Check Output Empty
    """
    tbl = mem_gpkg.create_table('tbl')
    with catch_warnings(record=True) as ws:
        simplefilter('always')
        _check_output(tbl)
        assert len(ws) == 1
        w, = ws
        assert issubclass(w.category, OperationsWarning)
# End test_check_output_empty function


def test_check_output_not_exists(mem_gpkg):
    """
    Test Check Output not exists
    """
    tbl = Table(mem_gpkg, name='aaaaa1111111111')
    with catch_warnings(record=True) as ws:
        simplefilter('always')
        _check_output(tbl)
        assert len(ws) == 1
        w, = ws
        assert issubclass(w.category, OperationsWarning)
# End test_check_output_not_exists function


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
def test_validate_element_data_type(world_features, world_tables, mem_gpkg, name, exists, has_content):
    """
    Test validate element
    """
    @validate_element('element', exists=exists, has_content=has_content)
    def element_function(element):
        pass
    if name is None:
        names = element_names(mem_gpkg)
        e = Table.create(mem_gpkg, name=make_unique_name(str(name), names=names), fields=())
    elif not name:
        e = Table(mem_gpkg, name='asdf')
    else:
        e = world_features[name] or world_tables[name]
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
def test_validate_geopackage(mem_gpkg, exists):
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
    geo_function(mem_gpkg)
    geo_function(MemoryGeoPackage.create())
# End test_validate_geopackage function


@mark.parametrize('exists', [
    True, False
])
def test_validate_geopackage_with_current(mem_gpkg, exists):
    """
    Test validate geopackage where current-workspace is used
    """
    @validate_geopackage(exists=exists)
    def geo_function(geopackage):
        return geopackage
    with raises(TypeError):
        geo_function(None)
    assert geo_function(mem_gpkg) is mem_gpkg
    with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
        assert geo_function(None) is mem_gpkg
    with raises(TypeError):
        with Swap(Setting.CURRENT_WORKSPACE, None):
            geo_function(None)
# End test_validate_geopackage_with_current function


@mark.parametrize('name, geometry_types, throws', [
    ('admin_a', (), False),
    ('roads_l', (), False),
    ('airports_p', (), False),
    ('admin_a', GEOM_TYPE_POLYGONS, False),
    ('roads_l', GEOM_TYPE_LINES, False),
    ('airports_p', GEOM_TYPE_POINTS, False),
    ('admin_a', GeometryType.polygon, False),
    ('roads_l', GeometryType.linestring, False),
    ('airports_p', GeometryType.point, False),
    ('cities_p', GEOM_TYPE_POLYGONS, True),
    (None, GEOM_TYPE_POLYGONS, True),
])
def test_validate_feature_class_geometry(world_features, name, geometry_types, throws):
    """
    Test validate feature class geometry
    """
    @validate_feature_class('feature_class', geometry_types=geometry_types)
    def fc_function(feature_class):
        return feature_class
    fc = world_features[name]
    if throws:
        with raises((ValueError, TypeError)):
            fc_function(fc)
    else:
        assert fc_function(fc) is fc
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
        return feature_class
    fc = world_features[name]
    if has_z or has_m:
        with raises(ValueError):
            fc_function(fc)
    else:
        assert fc_function(fc) is fc
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


@mark.parametrize('single, field', [
    (True, 'ID'),
    (False, 'ID'),
    (False, ['ID']),
])
def test_validate_field_data_type_and_string_name(inputs, single, field):
    """
    Test validate field data type
    """
    fc = inputs['intersect_a']
    @validate_field('fld', data_types=TEXT_AND_NUMBERS, single=single, element_name='element')
    def field_function(fld, element):
        return fld
    result = field_function(field, element=fc)
    if single:
        assert isinstance(result, Field)
    else:
        assert all(isinstance(f, Field) for f in result)
# End test_validate_field_data_type_and_string_name function


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
    tbl = world_tables['admin']
    if throws:
        with raises(ValueError):
            field_function(tbl, fld)
    else:
        field_function(tbl, fld)
# End test_validate_field_single_field function


def test_validate_table_with_setting(world_tables, world_features):
    """
    Test validate table using setting
    """
    @validate_table('table')
    def table_function(table):
        return table
    name = 'admin'
    assert isinstance(table_function(world_tables[name]), Table)
    with raises(TypeError):
        table_function(name)
    with Swap(Setting.CURRENT_WORKSPACE, world_tables):
        assert isinstance(table_function(name), Table)
    with raises(TypeError):
        with Swap(Setting.CURRENT_WORKSPACE, world_features):
            table_function(name)
# End test_validate_table_with_setting function


@mark.parametrize('fld, exists, throws', [
    (Field('NAME', data_type=SQLFieldType.text), True, False),
    (Field('name', data_type=SQLFieldType.text), True, False),
    (Field('asdf', data_type=SQLFieldType.text), True, True),
    (Field('NAME', data_type=SQLFieldType.text), False, False),
    (Field('name', data_type=SQLFieldType.text), False, False),
    (Field('asdf', data_type=SQLFieldType.text), False, True),
    ('asdf', True, True),
    ('NAME', True, False),
    (('NAME', 'ANOTHER_NAME'), True, True),
])
def test_validate_field_multiple_fields(world_tables, fld, exists, throws):
    """
    Test validate field multiple fields
    """
    @validate_table('table')
    @validate_field('fields', element_name='table', single=False, exists=exists)
    def field_function(table, fields):
        pass
    tbl = world_tables['admin']
    if throws:
        with raises(ValueError):
            field_function(tbl, fld)
    else:
        field_function(tbl, fld)
# End test_validate_field_multiple_fields function


def test_validate_same_crs(mem_gpkg):
    """
    Test validate same crs
    """
    @validate_same_crs('a', 'b')
    def crs_function(a, b):
        pass
    srs_a = mem_gpkg.spatial_references[4326]
    srs_b = SpatialReferenceSystem(name='NAD27', organization='EPSG', org_coord_sys_id=4267, definition=CRS(4267).to_wkt())
    fc_a = mem_gpkg.create_feature_class('aaa', srs=srs_a)
    fc_b = mem_gpkg.create_feature_class('bbb', srs=srs_b)
    with raises(OperationsError):
        crs_function(fc_a, fc_b)
# End test_validate_same_crs function


@mark.parametrize('value, expected', [
    (None, None),
    (0, 0.),
    (-10, 0.),
    ('10', 10.),
])
def test_validate_xy_tolerance_sans_setting(value, expected):
    """
    Test validate xy tolerance (sans setting)
    """
    @validate_xy_tolerance()
    def xy_function(xy_tolerance=None):
        return xy_tolerance

    assert xy_function(value) == expected
# End test_validate_xy_tolerance_sans_setting function

@mark.parametrize('value, expected, throws', [
    (None, None, True),
    ('ALL', AttributeOption.ALL, False),
    (AttributeOption.ONLY_FID, AttributeOption.ONLY_FID, False),
    (10, None, True),
])
def test_validate_enumeration(value, expected, throws):
    """
    Test validate enumeration
    """
    @validate_enumeration('option', AttributeOption)
    def enum_function(option):
        return option
    if throws:
        with raises(ValueError):
            enum_function(value)
    else:
        assert enum_function(value) == expected
# End test_validate_enumeration function


@mark.parametrize('value, swap_value, expected', [
    (None, None, None),
    (0, None, 0.),
    (-10, None, 0.),
    ('10', None, 10.),
])
def test_validate_xy_tolerance_with_setting(value, swap_value, expected):
    """
    Test validate xy tolerance (with setting)
    """
    @validate_xy_tolerance()
    def xy_function(xy_tolerance=None):
        return xy_tolerance
    with Swap(Setting.XY_TOLERANCE, swap_value):
        assert xy_function(value) == expected
    with Swap(Setting.XY_TOLERANCE, value):
        assert xy_function(None) == expected
    with Swap(Setting.XY_TOLERANCE, value):
        assert xy_function(123) == 123.
# End test_validate_xy_tolerance_with_setting function


def test_validate_result(inputs):
    """
    Test validate result
    """
    fc = inputs['updater_a']
    @validate_result()
    def result_function(result):
        return result
    assert result_function(fc) == fc
# End test_validate_result function


@mark.parametrize('source_name, operator_name, same, throws, expected', [
    ('admin_a', 'admin_mp_a', False, False, (2, 2)),
    ('admin_a', 'airports_p', False, True, ()),
    ('airports_p', 'admin_a', False, False, (0, 2)),
    ('admin_a', 'admin_mp_a', True, False, (2, 2)),
    ('admin_a', 'airports_p', True, True, ()),
    ('airports_p', 'admin_a', True, True, ()),
])
def test_validate_geometry_dimension(world_features, source_name, operator_name, same, throws, expected):
    """
    Test validate geometry dimension
    """
    source = world_features[source_name]
    operator = world_features[operator_name]
    @validate_geometry_dimension('s', 'o', same=same, strict=True)
    def geom_function(s, o):
        return get_geometry_dimension(s), get_geometry_dimension(o)

    if throws:
        with raises(OperationsError):
            geom_function(source, operator)
    else:
        assert geom_function(source, operator) == expected
# End test_validate_geometry_dimension function


@mark.parametrize('source_name, operator_name, option, throws', [
    ('admin_a', 'intersect_a', OutputTypeOption.SAME, False),
    ('rivers_l', 'intersect_a', OutputTypeOption.SAME, False),
    ('airports_p', 'intersect_a', OutputTypeOption.SAME, False),
    ('rivers_l', 'rivers_portion_l', OutputTypeOption.SAME, False),
    ('airports_p', 'rivers_portion_l', OutputTypeOption.SAME, False),
    ('airports_p', 'river_p', OutputTypeOption.SAME, False),
    ('admin_a', 'intersect_a', OutputTypeOption.LINE, False),
    ('rivers_l', 'intersect_a', OutputTypeOption.LINE, False),
    ('airports_p', 'intersect_a', OutputTypeOption.LINE, True),
    ('rivers_l', 'rivers_portion_l', OutputTypeOption.LINE, False),
    ('airports_p', 'rivers_portion_l', OutputTypeOption.LINE, True),
    ('airports_p', 'river_p', OutputTypeOption.LINE, True),
    ('admin_a', 'intersect_a', OutputTypeOption.POINT, False),
    ('rivers_l', 'intersect_a', OutputTypeOption.POINT, False),
    ('airports_p', 'intersect_a', OutputTypeOption.POINT, False),
    ('rivers_l', 'rivers_portion_l', OutputTypeOption.POINT, False),
    ('airports_p', 'rivers_portion_l', OutputTypeOption.POINT, False),
    ('airports_p', 'river_p', OutputTypeOption.POINT, False),
])
def test_validate_output_type(inputs, world_features, source_name, operator_name, option, throws):
    """
    Test validate output type
    """
    source = world_features[source_name]
    operator = inputs[operator_name]
    @validate_output_type('option', 's')
    def geom_function(s, o, option):
        return option

    if throws:
        with raises(OperationsError):
            geom_function(source, operator, option)
    else:
        assert geom_function(source, operator, option) == option
# End test_validate_output_type function


if __name__ == '__main__':  # pragma: no cover
    pass
