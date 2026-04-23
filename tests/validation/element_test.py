# -*- coding: utf-8 -*-
"""
Tests for Element Validation
"""

from warnings import catch_warnings, simplefilter

from pytest import raises, mark

from fudgeo import FeatureClass, Table
from fudgeo.enumeration import ShapeType

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.geometry.validate import get_geometry_dimension

from spyops.shared.exception import OperationsError, OperationsWarning
from spyops.shared.field import (
    GEOM_TYPE_LINES, GEOM_TYPE_POINTS,
    GEOM_TYPE_POLYGONS)
from spyops.shared.util import element_names, make_unique_name
from spyops.validation import (
    validate_element, validate_elements, validate_feature_class,
    validate_geometry_dimension, validate_overwrite_input, validate_table)
from spyops.validation.result import _check_output


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


@mark.parametrize('exists, has_content', [
    (True, True),
    (True, False),
    (False, False),
    (False, True),
])
def test_validate_elements_type(exists, has_content):
    """
    Test validate elements type
    """
    @validate_elements('element', exists=exists, has_content=has_content)
    def element_function(element):
        pass
    with raises(TypeError):
        element_function(element=Ellipsis)
# End test_validate_elements_type function


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


@mark.parametrize('name, exists, has_content', [
    ('admin_a', True, True),
    ('admin_a', True, False),
    ('admin_a', False, False),
    ('admin_a', False, True),
    ('admin', True, True),
    ('admin', True, False),
    ('admin', False, False),
    ('admin', False, True),
    (None, True, False),
    (None, False, False),
    (None, False, True),
    ('', True, True),
    ('', True, False),
    ('', False, False),
    ('', False, True),
])
def test_validate_elements_data_type(world_features, world_tables, mem_gpkg, name, exists, has_content):
    """
    Test validate element
    """
    @validate_elements('element', exists=exists, has_content=has_content)
    def element_function(element):
        pass
    if name is None:
        names = element_names(mem_gpkg)
        e = Table.create(mem_gpkg, name=make_unique_name(str(name), names=names), fields=())
    elif not name:
        e = Table(mem_gpkg, name='asdf')
    else:
        e = world_features[name] or world_tables[name]
    if name == '' and exists:
        with raises(ValueError):
            element_function(element=e)
    else:
        element_function(element=e)
# End test_validate_elements_data_type function


@mark.parametrize('name, geometry_types, throws', [
    ('admin_a', (), False),
    ('roads_l', (), False),
    ('airports_p', (), False),
    ('admin_a', GEOM_TYPE_POLYGONS, False),
    ('roads_l', GEOM_TYPE_LINES, False),
    ('airports_p', GEOM_TYPE_POINTS, False),
    ('admin_a', ShapeType.polygon, False),
    ('roads_l', ShapeType.linestring, False),
    ('airports_p', ShapeType.point, False),
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


def test_validate_overwrite_input(world_features, inputs, mem_gpkg):
    """
    Test validate_overwrite_input
    """
    source = world_features['admin_a']
    operator = inputs['clipper_a']

    @validate_feature_class('s')
    @validate_feature_class('o')
    @validate_feature_class('t', exists=False)
    @validate_overwrite_input('t', 's', 'o')
    def geom_function(s, o, t):
        return True

    target = inputs['clipper_a']
    with raises(OperationsError):
        geom_function(source, operator, target)

    target = FeatureClass(geopackage=source.geopackage, name='lmnop')
    assert geom_function(source, operator, target)

    op = operator.copy(name=operator.name, geopackage=mem_gpkg)
    target = FeatureClass(geopackage=mem_gpkg, name='lmnop')
    assert geom_function(source, op, target)

    target = FeatureClass(geopackage=mem_gpkg, name=op.name)
    with raises(OperationsError):
        assert geom_function(source, op, target)
# End test_validate_overwrite_input function


if __name__ == '__main__':  # pragma: no cover
    pass
