# -*- coding: utf-8 -*-
"""
Test for Overlay Query Classes
"""


from fudgeo import FeatureClass
from pytest import mark

from geomio.analysis.overlay import intersect
from geomio.query.overlay import QueryIntersectClassic, QueryIntersectPairwise
from geomio.shared.enumeration import AttributeOption
from geomio.shared.field import get_geometry_column_name

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
# End TestQueryIntersectClassic class


if __name__ == '__main__':  # pragma: no cover
    pass
