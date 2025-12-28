# -*- coding: utf-8 -*-
"""
Test for Overlay Query Classes
"""


from fudgeo import FeatureClass
from pytest import mark

from geomio.query.overlay import QueryIntersectClassic, QueryIntersectPairwise
from geomio.shared.constant import DUNDER_FID
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
        query = QueryIntersectPairwise(source=cites, target=target, operator=operator,
                                       attribute_option=option)
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
        query = QueryIntersectPairwise(source=admin, target=target, operator=operator,
                                       attribute_option=option)
        fields = query._get_unique_fields()

        assert [f.name for f in fields] == names
    # End test_unique_fields method

    def test_target_empty(self, inputs, world_features, mem_gpkg):
        """
        Test target empty
        """
        operator = inputs['intersect_a']
        cites = world_features['cities_p']
        target = FeatureClass(geopackage=mem_gpkg, name='cities_____p')
        query = QueryIntersectPairwise(source=cites, target=target, operator=operator,
                                       attribute_option=AttributeOption.ALL)
        assert isinstance(query.target_empty, FeatureClass)
        assert query.target_empty
        assert not len(query.target_empty)
        assert query.insert.strip().startswith('INSERT INTO cities_____p')
    # End test_target_empty method
# End TestQueryIntersectPairwise class


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
            attribute_option=AttributeOption.ALL)
        operator = query.operator
        assert len(operator) == 9
        source = query.source
        assert len(source) == 268
    # End test_planarize method

    @mark.parametrize('option, input_names, planar_names', [
        (AttributeOption.ALL, 'geom "[MultiPolygon]", fid AS "__fid__", id', 'SHAPE "[Polygon]", "__fid__", ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.SANS_FID, 'geom "[MultiPolygon]", fid AS "__fid__", id', 'SHAPE "[Polygon]", ID, NAME, "WHEN", EXAMPLE_JSON, BOB, NOT_NOW'),
        (AttributeOption.ONLY_FID, 'geom "[MultiPolygon]", fid AS "__fid__", id', 'SHAPE "[Polygon]", "__fid__"'),
    ])
    def test_field_names_and_count(self, inputs, mem_gpkg, option, input_names, planar_names):
        """
        Test field names and count
        """
        source = inputs['int_flavor_a']
        query = QueryIntersectClassic(
            source, target=None,
            operator=inputs['intersect_a'],
            attribute_option=option)
        *_, names = query._field_names_and_count(source)
        assert names == input_names
        operator = query.operator
        *_, names = query._field_names_and_count(operator)
        assert names == planar_names
    # End test_field_names_and_count method

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
            attribute_option=option)
        assert query.target.field_names == names
    # End test_target_fields method

    @mark.parametrize('option, source_names, target_names', [
        (AttributeOption.ALL, [DUNDER_FID, 'id'], [DUNDER_FID, 'ID', 'NAME', 'WHEN', 'EXAMPLE_JSON', 'BOB', 'NOT_NOW']),
        (AttributeOption.SANS_FID, ['id'], ['ID', 'NAME', 'WHEN', 'EXAMPLE_JSON', 'BOB', 'NOT_NOW']),
        (AttributeOption.ONLY_FID, [DUNDER_FID], [DUNDER_FID]),
    ])
    def test_get_fields(self, inputs, mem_gpkg, option, source_names, target_names):
        """
        Test get fields
        """
        source = inputs['int_flavor_a']
        operator = inputs['intersect_a']
        query = QueryIntersectClassic(
            source, target=None,
            operator=operator,
            attribute_option=option)
        fields = query._get_fields(source)
        assert [f.name for f in fields] == ['id']
        fields = query._get_fields(query.source)
        assert [f.name for f in fields] == source_names

        fields = query._get_fields(operator)
        assert [f.name for f in fields] == ['ID', 'NAME', 'WHEN', 'EXAMPLE_JSON', 'BOB', 'NOT_NOW']
        fields = query._get_fields(query.operator)
        assert [f.name for f in fields] == target_names
    # End test_get_fields method
# End TestQueryIntersectClassic class


if __name__ == '__main__':  # pragma: no cover
    pass
