# -*- coding: utf-8 -*-
"""
Test for Overlay Query Classes
"""


from fudgeo import FeatureClass
from pytest import mark

from geomio.query.overlay import (
    PlanarizeOperator, PlanarizeSource, QueryIntersectClassic,
    QueryIntersectPairwise)
from geomio.shared.enumeration import AttributeOption

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
        target = FeatureClass(geopackage=mem_gpkg, name='adminaaaaaa')
        query = QueryIntersectPairwise(
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
        target = FeatureClass(geopackage=mem_gpkg, name='adminaaaaaa')
        query = QueryIntersectPairwise(
            source=admin, target=target, operator=operator,
            attribute_option=option, xy_tolerance=None)
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
            attribute_option=AttributeOption.ALL, xy_tolerance=None)
        assert isinstance(query.target_empty, FeatureClass)
        assert query.target_empty
        assert not len(query.target_empty)
        assert query.insert.strip().startswith('INSERT INTO cities_____p')
    # End test_target_empty method
# End TestQueryIntersectPairwise class


class TestPlanarize:
    """
    Test Planarize
    """
    @mark.parametrize('option', [
        AttributeOption.ALL,
        AttributeOption.SANS_FID,
        AttributeOption.ONLY_FID,
    ])
    def test_planarize_source(self, inputs, mem_gpkg, option):
        """
        Test Planarize Source
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        ps = PlanarizeSource(source=source, operator=operator, xy_tolerance=None)
        assert ps.temporary_fid_field.name == 'fid_int_flavor_a'
        fc = ps()
        assert fc.field_names == ['fid', 'SHAPE', 'fid_int_flavor_a', 'id']
        assert len(fc) == 268
    # End test_planarize_source method

    @mark.parametrize('option', [
        AttributeOption.ALL,
        AttributeOption.SANS_FID,
        AttributeOption.ONLY_FID,
    ])
    def test_planarize_operator(self, inputs, mem_gpkg, option):
        """
        Test Planarize Operator
        """
        operator = inputs['intersect_a']
        source = inputs['int_flavor_a']
        po = PlanarizeOperator(source=source, operator=operator, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_intersect_a'
        fc = po()
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
        po = PlanarizeOperator(source=source, operator=operator, xy_tolerance=None)
        assert po.temporary_fid_field.name == 'fid_intersect_holes_a'
        fc = po()
        assert fc.field_names == [
            'fid', 'SHAPE', 'fid_intersect_holes_a', 'ID', 'NAME', 'WHEN',
            'EXAMPLE_JSON', 'BOB', 'NOT_NOW']
        assert len(fc) == 9
    # End test_planarize_operator_holes method
# End TestPlanarize class


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
            attribute_option=AttributeOption.ALL, xy_tolerance=None)
        source = query.source
        assert len(source) == 268
        operator = query.operator
        assert len(operator) == 9
    # End test_planarize method

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
            attribute_option=option, xy_tolerance=None)
        assert query.target.field_names == names
    # End test_target_fields method
# End TestQueryIntersectClassic class


if __name__ == '__main__':  # pragma: no cover
    pass
