# -*- coding: utf-8 -*-
"""
Test for Overlay Query Classes
"""


from fudgeo import FeatureClass, Field
from fudgeo.enumeration import SQLFieldType
from pytest import mark, param

from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.environment.enumeration import (
    OutputMOption, OutputZOption, Setting)
from spyops.query.overlay import (
    PlanarizeGeneralOperator, PlanarizeGeneralSource, PlanarizePolygonOperator,
    PlanarizePolygonSource, QueryIntersectClassic, QueryIntersectPairwise,
    QuerySymmetricalDifferenceClassic, QuerySymmetricalDifferencePairwise,
    QueryUnionClassic, QueryUnionPairwise)
from spyops.shared.element import copy_element
from spyops.shared.enumeration import AttributeOption, OutputTypeOption

pytestmark = [mark.overlay, mark.query]


class TestQueryIntersectPairwise:
    """
    Test Query Intersect Pairwise
    """
    @mark.parametrize('option, names', [
        (AttributeOption.ALL, 'geom "[Polygon]", fid, ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.ONLY_FID, 'geom "[Polygon]", fid'),
        (AttributeOption.SANS_FID, 'geom "[Polygon]", ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
    ])
    def test_field_names_and_count(self, inputs, world_features, mem_gpkg, option, names):
        """
        Test field names and count
        """
        operator = inputs['intersect_a']
        cites = world_features['cities_p']
        target = FeatureClass(geopackage=mem_gpkg, name='cities_1234_p')
        query = QueryIntersectPairwise(
            source=cites, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        *_, select = query._field_names_and_count(operator)
        assert select == names
    # End test_field_names_and_count method

    @mark.parametrize('option, names', [
        (AttributeOption.ALL, [
            'fid_admin_a', 'FEATURE_ID', 'PART_ID', 'NAME', 'COUNTRY',
            'ISO_CODE', 'ISO_CC', 'ISO_SUB', 'ADMINTYPE', 'DISPUTED', 'NOTES',
            'AUTONOMOUS', 'COUNTRYAFF', 'CONTINENT', 'LAND_TYPE', 'LAND_RANK',
            'fid_intersect_a', 'ID', 'NAME_1', 'WHEN', 'EXAMPLE_JSON', 'BOB',
            'NOT_NOW']),
        (AttributeOption.ONLY_FID, ['fid_admin_a', 'fid_intersect_a']),
        (AttributeOption.SANS_FID, [
            'FEATURE_ID', 'PART_ID', 'NAME', 'COUNTRY', 'ISO_CODE', 'ISO_CC',
            'ISO_SUB', 'ADMINTYPE', 'DISPUTED', 'NOTES', 'AUTONOMOUS',
            'COUNTRYAFF', 'CONTINENT', 'LAND_TYPE', 'LAND_RANK', 'ID', 'NAME_1',
            'WHEN', 'EXAMPLE_JSON', 'BOB', 'NOT_NOW']),
    ])
    def test_unique_fields(self, inputs, world_features, mem_gpkg, option, names):
        """
        Test field names and count
        """
        operator = inputs['intersect_a']
        admin = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='adminaaaaaa')
        query = QueryIntersectPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        fields = query._get_unique_fields()

        assert [f.name for f in fields] == names
    # End test_unique_fields method

    @mark.parametrize('option, names', [
        (AttributeOption.ALL, [
            'fid_intersect_a', 'ID', 'NAME', 'WHEN', 'EXAMPLE_JSON', 'BOB',
            'NOT_NOW', 'fid_intersect_a_1', 'ID_1', 'NAME_1', 'WHEN_1',
            'EXAMPLE_JSON_1', 'BOB_1', 'NOT_NOW_1']),
        (AttributeOption.ONLY_FID, ['fid_intersect_a', 'fid_intersect_a_1']),
    ])
    def test_unique_fields_same(self, inputs, world_features, mem_gpkg, option, names):
        """
        Test field names and count using same source and operator
        """
        admin = operator = inputs['intersect_a']
        target = FeatureClass(geopackage=mem_gpkg, name='adminaaaaaa')
        query = QueryIntersectPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        fields = query._get_unique_fields()

        assert [f.name for f in fields] == names
    # End test_unique_fields_same method

    def test_target_empty(self, inputs, world_features, mem_gpkg):
        """
        Test target empty
        """
        operator = inputs['intersect_a']
        cites = world_features['cities_p']
        target = FeatureClass(geopackage=mem_gpkg, name='cities_____p')
        query = QueryIntersectPairwise(
            source=cites, target=target, operator=operator,
            attribute_option=AttributeOption.ALL, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        assert isinstance(query.target_empty, FeatureClass)
        assert query.target_empty
        assert not len(query.target_empty)
        assert ' INTO cities_____p' in query.insert
    # End test_target_empty method
# End TestQueryIntersectPairwise class


class TestPlanarizePolygons:
    """
    Test Planarize Polygons
    """
    def test_planarize_source(self, inputs, mem_gpkg):
        """
        Test Planarize Source
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        ps = PlanarizePolygonSource(source=source, operator=operator, use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_int_flavor_a'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == ['fid', 'SHAPE', 'fid_int_flavor_a', 'id']
        assert len(fc) == 268
    # End test_planarize_source method

    def test_planarize_source_zm(self, grid_index, ntdb_zm_meh, mem_gpkg):
        """
        Test Planarize Source
        """
        operator = grid_index['grid_a']
        source = ntdb_zm_meh['structures_zm_a']
        ps = PlanarizePolygonSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_structures_zm_a'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_structures_zm_a', 'OBJECTID',
            'ENTITY', 'ENTITY_NAME', 'VALDATE', 'PROVIDER', 'DATANAME',
            'ACCURACY', 'FILE_NAME', 'CODE']
        assert len(fc) == 1550
    # End test_planarize_source_zm method

    def test_planarize_operator(self, inputs, mem_gpkg):
        """
        Test Planarize Operator
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        po = PlanarizePolygonOperator(source=source, operator=operator,
                                      use_full_extent=False, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_intersect_a'
        fc, fid_field = po()
        assert fid_field.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_intersect_a', 'ID', 'NAME', 'WHEN',
            'EXAMPLE_JSON', 'BOB', 'NOT_NOW']
        assert len(fc) == 9
    # End test_planarize_operator method

    def test_planarize_operator_holes(self, inputs, mem_gpkg):
        """
        Test Planarize Operator using feature class with holes
        """
        operator = inputs['intersect_holes_a']
        source = inputs['int_flavor_a']
        po = PlanarizePolygonOperator(source=source, operator=operator,
                                      use_full_extent=False, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_intersect_holes_a'
        fc, fid_field = po()
        assert fid_field.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_intersect_holes_a', 'ID', 'NAME', 'WHEN',
            'EXAMPLE_JSON', 'BOB', 'NOT_NOW']
        assert len(fc) == 13
    # End test_planarize_operator_holes method

    def test_planarize_source_multi_part(self, inputs, world_features, mem_gpkg):
        """
        Test Planarize Source Multi Part on a non FID column
        """
        operator = inputs['rivers_portion_l']
        source = world_features['admin_mp_a']
        ps = PlanarizePolygonSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'OBJECTID_admin_mp_a'
    # End test_planarize_source_multi_part method
# End TestPlanarizePolygons class


class TestPlanarizeGeneral:
    """
    Test Planarize Line Strings and Points
    """
    def test_planarize_source(self, inputs, world_features, mem_gpkg):
        """
        Test Planarize Source
        """
        operator = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        ps = PlanarizeGeneralSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_rivers_l'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_rivers_l', 'FEATURE_ID', 'PART_ID',
            'NAME', 'SYSTEM', 'MILES', 'KILOMETERS']
        assert len(fc) == 135
    # End test_planarize_source method

    def test_planarize_operator(self, inputs, world_features, mem_gpkg):
        """
        Test Planarize Operator
        """
        operator = inputs['rivers_portion_l']
        source = world_features['rivers_l']
        po = PlanarizeGeneralOperator(source=source, operator=operator,
                                      use_full_extent=False, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_rivers_portion_l'
        fc, fid_fld = po()
        assert fid_fld.name == 'fid'
        assert fc.field_names == ['fid', 'SHAPE', 'fid_rivers_portion_l', 'NAME', 'SYSTEM']
        assert len(fc) == 134
    # End test_planarize_operator method

    def test_planarize_source_point(self, inputs, mem_gpkg):
        """
        Test Planarize Source Point
        """
        operator = inputs['rivers_portion_l']
        source = inputs['river_p']
        ps = PlanarizeGeneralSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_river_p'
        fc, fid_fld = ps()
        assert fid_fld.name == 'fid'
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_river_p', 'NAME', 'SYSTEM', 'vertex_index',
            'vertex_part', 'vertex_part_index', 'distance', 'angle']
        assert len(fc) == 20620
    # End test_planarize_source_point method

    def test_planarize_source_multi_part(self, inputs, world_features, mem_gpkg):
        """
        Test Planarize Source Multi Part on a non FID column
        """
        operator = inputs['rivers_portion_l']
        source = world_features['admin_mp_a']
        ps = PlanarizeGeneralSource(source=source, operator=operator,
                                    use_full_extent=False, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'OBJECTID_admin_mp_a'
    # End test_planarize_source_multi_part method
# End TestPlanarizeGeneral class


class TestQueryIntersectClassic:
    """
    Test Query Intersect Classic
    """
    def test_planarize(self, inputs, mem_gpkg):
        """
        Test Planarize
        """
        query = QueryIntersectClassic(
            inputs['int_flavor_a'], target=None,
            operator=inputs['intersect_a'],
            attribute_option=AttributeOption.ALL, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        source = query.source
        assert len(source) == 268
        operator = query.operator
        assert len(operator) == 9
    # End test_planarize method

    def test_insert_planarize(self, inputs, mem_gpkg):
        """
        Test Planarize
        """
        query = QueryIntersectClassic(
            inputs['int_flavor_a'],
            target=FeatureClass(geopackage=mem_gpkg, name='lmno'),
            operator=inputs['intersect_a'],
            attribute_option=AttributeOption.ALL, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        assert 'INTO lmno(SHAPE, fid_int_flavor_a, id, fid_intersect_a,' in query.insert
    # End test_insert_planarize method

    def test_insert_general_planar(self, world_features, mem_gpkg):
        """
        Test insert statement when rolling through general planar
        """
        operator = world_features['cities_p']
        cites = world_features['cities_p']
        target = FeatureClass(geopackage=mem_gpkg, name='ceetees')
        query = QueryIntersectClassic(
            source=cites, target=target, operator=operator,
            attribute_option=AttributeOption.ALL, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        assert ' INTO ceetees(SHAPE, fid_cities_p, CITY_NAME, GMI_ADMIN, ' in query.insert.strip()
    # End test_insert_general_planar method

    @mark.parametrize('option, names', [
        (AttributeOption.ALL, ['fid', 'SHAPE', 'fid_int_flavor_a', 'id', 'fid_intersect_a', 'ID_1', 'NAME', 'WHEN', 'EXAMPLE_JSON', 'BOB', 'NOT_NOW']),
        (AttributeOption.SANS_FID, ['fid', 'SHAPE', 'id', 'ID_1', 'NAME', 'WHEN', 'EXAMPLE_JSON', 'BOB', 'NOT_NOW']),
        (AttributeOption.ONLY_FID, ['fid', 'SHAPE', 'fid_int_flavor_a', 'fid_intersect_a'] ),
    ])
    def test_target_fields(self, inputs, mem_gpkg, option, names):
        """
        Test field names and count
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        query = QueryIntersectClassic(
            inputs['int_flavor_a'], target=target,
            operator=inputs['intersect_a'],
            attribute_option=option, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        assert query.target.field_names == names
    # End test_target_fields method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT SHAPE "[Polygon]", fid_int_flavor_a, id'),
        (AttributeOption.SANS_FID, 'SELECT SHAPE "[Polygon]", id'),
        (AttributeOption.ONLY_FID, 'SELECT SHAPE "[Polygon]", fid_int_flavor_a'),
    ])
    def test_select_source(self, inputs, mem_gpkg, option, sql):
        """
        Test source select sql
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        query = QueryIntersectClassic(
            inputs['int_flavor_a'], target=target,
            operator=inputs['intersect_a'],
            attribute_option=option, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        assert sql in query.select
    # End test_select_source method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT SHAPE "[Polygon]", fid_intersect_a, ID, NAME, "WHEN"'),
        (AttributeOption.SANS_FID, 'SELECT SHAPE "[Polygon]", ID, NAME, "WHEN"'),
        (AttributeOption.ONLY_FID, 'SELECT SHAPE "[Polygon]", fid_intersect_a'),
    ])
    def test_select_operator(self, inputs, mem_gpkg, option, sql):
        """
        Test operator select sql
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        query = QueryIntersectClassic(
            inputs['int_flavor_a'], target=target,
            operator=inputs['intersect_a'],
            attribute_option=option, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        assert sql in query.select_operator
    # End test_select_operator method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, ' INTO all_target(SHAPE, fid_int_flavor_a, id, fid_intersect_a, ID_1'),
        (AttributeOption.SANS_FID, ' INTO sans_fid_target(SHAPE, id, ID_1, '),
        (AttributeOption.ONLY_FID, ' INTO only_fid_target(SHAPE, fid_int_flavor_a, fid_intersect_a)'),
    ])
    def test_insert(self, inputs, mem_gpkg, option, sql):
        """
        Test insert sql
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        query = QueryIntersectClassic(
            inputs['int_flavor_a'], target=target,
            operator=inputs['intersect_a'],
            attribute_option=option, xy_tolerance=None,
            output_type_option=OutputTypeOption.SAME)
        assert sql in query.insert
    # End test_insert method
# End TestQueryIntersectClassic class


class TestQuerySymmetricalDifferencePairwise:
    """
    Test QuerySymmetricalDifferencePairwise
    """
    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT SHAPE "[Polygon]", fid, ID'),
        (AttributeOption.ONLY_FID, 'SELECT SHAPE "[Polygon]", fid'),
        (AttributeOption.SANS_FID, 'SELECT SHAPE "[Polygon]", ID'),
    ])
    def test_disjoint_source(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Disjoint Source
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferencePairwise(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        disjoint = query._disjoint_source
        assert sql in disjoint
        assert source.name in disjoint
    # End test_disjoint_source method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT geom "[Polygon]", fid, ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.ONLY_FID, 'SELECT geom "[Polygon]", fid'),
        (AttributeOption.SANS_FID, 'SELECT geom "[Polygon]", ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
    ])
    def test_disjoint_operator(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Disjoint Operator
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferencePairwise(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        disjoint = query._disjoint_operator
        assert sql in disjoint
        assert operator.name in disjoint
    # End test_disjoint_operator method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'all_target(SHAPE, fid_clipper_a, ID'),
        (AttributeOption.ONLY_FID, 'only_fid_target(SHAPE, fid_clipper_a'),
        (AttributeOption.SANS_FID, 'sans_fid_target(SHAPE, ID'),
    ])
    def test_insert_source(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Insert Source
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferencePairwise(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        insert = query._insert_source
        assert sql in insert
        assert target.name in insert
    # End test_insert_source method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'all_target(SHAPE, fid_intersect_a, ID_1, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.ONLY_FID, 'only_fid_target(SHAPE, fid_intersect_a'),
        (AttributeOption.SANS_FID, 'sans_fid_target(SHAPE, ID_1, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
    ])
    def test_insert_operator(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Insert Operator
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferencePairwise(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        insert = query._insert_operator
        assert sql in insert
        assert target.name in insert
    # End test_insert_operator method

    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('hydro_a', 88),
        ('hydro_m_a', 88),
        ('hydro_z_a', 88),
        ('hydro_zm_a', 88),
        ('structures_a', 30),
        ('structures_m_a', 30),
        ('structures_z_a', 30),
        ('structures_zm_a', 30),
        ('structures_m_ma', 10),
        ('structures_z_ma', 10),
        ('structures_zm_ma', 10),
    ])
    @mark.parametrize('op_name', [
        'grid_a',
        param('grid_m_a', marks=mark.large),
        param('grid_z_a', marks=mark.large),
        'grid_zm_a',
    ])
    @mark.parametrize('output_z', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_target_full_disjoint_query(self, grid_index, ntdb_zm_tile, mem_gpkg,
                                        fc_name, count, op_name,
                                        output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm_tile[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        source.add_spatial_index()
        operator = copy_element(
            grid_index[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082O01-6'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            query = QuerySymmetricalDifferencePairwise(
                source, target=target, operator=operator,
                attribute_option=option, xy_tolerance=None)
            full = query.target_full
        assert full.has_z == zm.z_enabled
        assert full.has_m == zm.m_enabled
        assert full.count == count
    # End test_target_full_disjoint_query method
# End TestQuerySymmetricalDifferencePairwise class


class TestQuerySymmetricalDifferenceClassic:
    """
    Test QuerySymmetricalDifferenceClassic
    """
    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT SHAPE "[Polygon]", fid_clipper_a, ID'),
        (AttributeOption.ONLY_FID, 'SELECT SHAPE "[Polygon]", fid_clipper_a'),
        (AttributeOption.SANS_FID, 'SELECT SHAPE "[Polygon]", ID'),
    ])
    def test_disjoint_source(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Disjoint Source
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        disjoint = query._disjoint_source
        assert sql in disjoint
        assert source.name in disjoint
    # End test_disjoint_source method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT SHAPE "[Polygon]", fid_intersect_a, ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.ONLY_FID, 'SELECT SHAPE "[Polygon]", fid_intersect_a'),
        (AttributeOption.SANS_FID, 'SELECT SHAPE "[Polygon]", ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
    ])
    def test_disjoint_operator(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Disjoint Operator
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        disjoint = query._disjoint_operator
        assert sql in disjoint
        assert operator.name in disjoint
    # End test_disjoint_operator method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'all_target(SHAPE, fid_clipper_a, ID'),
        (AttributeOption.ONLY_FID, 'only_fid_target(SHAPE, fid_clipper_a'),
        (AttributeOption.SANS_FID, 'sans_fid_target(SHAPE, ID'),
    ])
    def test_insert_source(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Insert Source
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        insert = query._insert_source
        assert sql in insert
        assert target.name in insert
    # End test_insert_source method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'all_target(SHAPE, fid_intersect_a, ID_1, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.ONLY_FID, 'only_fid_target(SHAPE, fid_intersect_a'),
        (AttributeOption.SANS_FID, 'sans_fid_target(SHAPE, ID_1, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
    ])
    def test_insert_operator(self, inputs, mem_gpkg, option, sql):
        """
        Test SQL from Insert Operator
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = inputs['clipper_a']
        operator = inputs['intersect_a']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        insert = query._insert_operator
        assert sql in insert
        assert target.name in insert
    # End test_insert_operator method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT SHAPE "[Point]", fid_cities_p, CITY_NAME, GMI_ADMIN'),
        (AttributeOption.ONLY_FID, 'SELECT SHAPE "[Point]", fid_cities_p'),
        (AttributeOption.SANS_FID, 'SELECT SHAPE "[Point]", CITY_NAME, GMI_ADMIN'),
    ])
    def test_disjoint_source_general(self, world_features, mem_gpkg, option, sql):
        """
        Test SQL from Disjoint Source where general planar is used
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = world_features['cities_p']
        operator = world_features['airports_p']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        disjoint = query._disjoint_source
        assert sql in disjoint
        assert source.name in disjoint
    # End test_disjoint_source_general method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'SELECT SHAPE "[Point]", fid_airports_p, ISO_CC, Name, ICAO,'),
        (AttributeOption.ONLY_FID, 'SELECT SHAPE "[Point]", fid_airports_p'),
        (AttributeOption.SANS_FID, 'SELECT SHAPE "[Point]", ISO_CC, Name, ICAO,'),
    ])
    def test_disjoint_operator_general(self, world_features, mem_gpkg, option, sql):
        """
        Test SQL from Disjoint Operator where general planar is used
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = world_features['cities_p']
        operator = world_features['airports_p']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        disjoint = query._disjoint_operator
        assert sql in disjoint
        assert operator.name in disjoint
    # End test_disjoint_operator_general method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'all_target(SHAPE, fid_cities_p, CITY_NAME, GMI_ADMIN'),
        (AttributeOption.ONLY_FID, 'only_fid_target(SHAPE, fid_cities_p'),
        (AttributeOption.SANS_FID, 'sans_fid_target(SHAPE, CITY_NAME, GMI_ADMIN'),
    ])
    def test_insert_source_general(self, world_features, mem_gpkg, option, sql):
        """
        Test SQL from Insert Source where general planar is used
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = world_features['cities_p']
        operator = world_features['airports_p']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        insert = query._insert_source
        assert sql in insert
        assert target.name in insert
    # End test_insert_source_general method

    @mark.parametrize('option, sql', [
        (AttributeOption.ALL, 'all_target(SHAPE, fid_airports_p, ISO_CC, Name, ICAO,'),
        (AttributeOption.ONLY_FID, 'only_fid_target(SHAPE, fid_airports_p'),
        (AttributeOption.SANS_FID, 'sans_fid_target(SHAPE, ISO_CC, Name, ICAO,'),
    ])
    def test_insert_operator_general(self, world_features, mem_gpkg, option, sql):
        """
        Test SQL from Insert Operator where general planar is used
        """
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = world_features['cities_p']
        operator = world_features['airports_p']
        query = QuerySymmetricalDifferenceClassic(
            source, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        insert = query._insert_operator
        assert sql in insert
        assert target.name in insert
    # End test_insert_operator_general method

    @mark.zm
    @mark.parametrize('fc_name, count', [
        ('hydro_a', 88),
        ('hydro_m_a', 88),
        ('hydro_z_a', 88),
        ('hydro_zm_a', 88),
        ('structures_a', 34),
        ('structures_m_a', 34),
        ('structures_z_a', 34),
        ('structures_zm_a', 34),
        ('structures_m_ma', 34),
        ('structures_z_ma', 34),
        ('structures_zm_ma', 34),
    ])
    @mark.parametrize('op_name', [
        'grid_a',
        param('grid_m_a', marks=mark.large),
        param('grid_z_a', marks=mark.large),
        'grid_zm_a',
    ])
    @mark.parametrize('output_z', [
        param(OutputZOption.SAME, marks=mark.large),
        OutputZOption.ENABLED,
        param(OutputZOption.DISABLED, marks=mark.large),
    ])
    @mark.parametrize('output_m', [
        param(OutputMOption.SAME, marks=mark.large),
        OutputMOption.ENABLED,
        param(OutputMOption.DISABLED, marks=mark.large),
    ])
    def test_target_full_disjoint_query(self, grid_index, ntdb_zm_tile, mem_gpkg, fc_name,
                                        count, op_name, output_z, output_m):
        """
        Test target full, exercising process disjoint and handling
        different ZM dimensions
        """
        option = AttributeOption.ALL
        target = FeatureClass(geopackage=mem_gpkg, name=f'{str(option)}_target')
        source = copy_element(
            ntdb_zm_tile[fc_name], target=FeatureClass(mem_gpkg, fc_name),
            where_clause="""DATANAME IN ('082O01-1', '082O01-2')""")
        source.add_spatial_index()
        operator = copy_element(
            grid_index[op_name], target=FeatureClass(mem_gpkg, op_name),
            where_clause="""DATANAME = '082O01-6'""")
        operator.add_spatial_index()
        with (Swap(Setting.OUTPUT_Z_OPTION, output_z),
              Swap(Setting.OUTPUT_M_OPTION, output_m)):
            zm = zm_config(source, operator)
            query = QuerySymmetricalDifferenceClassic(
                source, target=target, operator=operator,
                attribute_option=option, xy_tolerance=None)
            full = query.target_full
        assert full.has_z == zm.z_enabled
        assert full.has_m == zm.m_enabled
        assert full.count == count
    # End test_target_full_disjoint_query method
# End TestQuerySymmetricalDifferenceClassic class


class TestQueryUnionPairwise:
    """
    Test QueryUnionPairwise
    """
    @mark.parametrize('option, names', [
        (AttributeOption.ALL, 'geom "[Polygon]", fid, ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.ONLY_FID, 'geom "[Polygon]", fid'),
        (AttributeOption.SANS_FID, 'geom "[Polygon]", ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
    ])
    def test_field_names_and_count(self, inputs, world_features, mem_gpkg, option, names):
        """
        Test field names and count
        """
        operator = inputs['intersect_a']
        admin = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='admin_target_a')
        query = QueryUnionPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        *_, select = query._field_names_and_count(operator)
        assert select == names
    # End test_field_names_and_count method

    @mark.parametrize('option, names', [
        (AttributeOption.ALL, [
            'fid_admin_a', 'FEATURE_ID', 'PART_ID', 'NAME', 'COUNTRY',
            'ISO_CODE', 'ISO_CC', 'ISO_SUB', 'ADMINTYPE', 'DISPUTED', 'NOTES',
            'AUTONOMOUS', 'COUNTRYAFF', 'CONTINENT', 'LAND_TYPE', 'LAND_RANK',
            'fid_intersect_a', 'ID', 'NAME_1', 'WHEN', 'EXAMPLE_JSON', 'BOB',
            'NOT_NOW']),
        (AttributeOption.ONLY_FID, ['fid_admin_a', 'fid_intersect_a']),
        (AttributeOption.SANS_FID, [
            'FEATURE_ID', 'PART_ID', 'NAME', 'COUNTRY', 'ISO_CODE', 'ISO_CC',
            'ISO_SUB', 'ADMINTYPE', 'DISPUTED', 'NOTES', 'AUTONOMOUS',
            'COUNTRYAFF', 'CONTINENT', 'LAND_TYPE', 'LAND_RANK', 'ID', 'NAME_1',
            'WHEN', 'EXAMPLE_JSON', 'BOB', 'NOT_NOW']),
    ])
    def test_unique_fields(self, inputs, world_features, mem_gpkg, option, names):
        """
        Test field names and count
        """
        operator = inputs['intersect_a']
        admin = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='admin_target_a')
        query = QueryUnionPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        fields = query._get_unique_fields()

        assert [f.name for f in fields] == names
    # End test_unique_fields method

    @mark.parametrize('option, names', [
        (AttributeOption.ALL, [
            'fid_intersect_a', 'ID', 'NAME', 'WHEN', 'EXAMPLE_JSON', 'BOB',
            'NOT_NOW', 'fid_intersect_a_1', 'ID_1', 'NAME_1', 'WHEN_1',
            'EXAMPLE_JSON_1', 'BOB_1', 'NOT_NOW_1']),
        (AttributeOption.ONLY_FID, ['fid_intersect_a', 'fid_intersect_a_1']),
    ])
    def test_unique_fields_same(self, inputs, world_features, mem_gpkg, option, names):
        """
        Test field names and count using same source and operator
        """
        admin = operator = inputs['intersect_a']
        target = FeatureClass(geopackage=mem_gpkg, name='admin_target_a')
        query = QueryUnionPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
        fields = query._get_unique_fields()
        assert [f.name for f in fields] == names
    # End test_unique_fields_same method

    def test_target_empty(self, inputs, world_features, mem_gpkg):
        """
        Test target empty, should be same object as target input
        """
        operator = inputs['intersect_a']
        admin = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='admin_target_a')
        query = QueryUnionPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=AttributeOption.ALL, xy_tolerance=None)
        assert isinstance(query.target_empty, FeatureClass)
        assert not query.target_empty.exists
        assert query.target_empty is target
        assert ' INTO admin_target_a' in query.insert
    # End test_target_empty method

    def test_input_fid(self, inputs, world_features, mem_gpkg):
        """
        Test Input FID values
        """
        operator = inputs['intersect_a']
        admin = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='admin_target_a')
        query = QueryUnionPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=AttributeOption.ALL, xy_tolerance=None)
        assert query.input_fid_source.name == 'fid'
        assert query.input_fid_operator.name == 'fid'
    # End test_input_fid method
# End TestQueryUnionPairwise class


class TestQueryUnionClassic:
    """
    Test QueryUnionClassic
    """
    def test_input_fid(self, inputs, world_features, mem_gpkg):
        """
        Test Input FID values
        """
        operator = inputs['intersect_a']
        admin = world_features['admin_a']
        target = FeatureClass(geopackage=mem_gpkg, name='admin_target_a')
        query = QueryUnionClassic(
            source=admin, source_fid=Field('asdf', data_type=SQLFieldType.integer),
            operator=operator, operator_fid=Field('lmno', data_type=SQLFieldType.integer),
            target=target,
            attribute_option=AttributeOption.ALL, xy_tolerance=None)
        assert query.input_fid_source.name == 'asdf'
        assert query.input_fid_operator.name == 'lmno'
    # End test_input_fid method
# End TestQueryUnionClassic class


if __name__ == '__main__':  # pragma: no cover
    pass
