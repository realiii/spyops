# -*- coding: utf-8 -*-
"""
Test for Generalization Query classes
"""


from fudgeo import FeatureClass, Field
from fudgeo.enumeration import FieldType
from pytest import mark

from spyops.query.management.generalization import QueryDissolve
from spyops.shared.stats import Median


pytestmark = [mark.generalization, mark.query, mark.management]


class TestQueryDissolve:
    """
    Test QueryDissolve
    """
    @staticmethod
    def _get_fields():
        """
        Get Fields
        """
        return [
            Field('NAME', data_type=FieldType.text),
            Field('COUNTRY', data_type=FieldType.text),
            Field('ISO_CODE', data_type=FieldType.text),
            Field('ISO_CC', data_type=FieldType.text),
            Field('ISO_SUB', data_type=FieldType.text),
            Field('DISPUTED', data_type=FieldType.mediumint),
            Field('CONTINENT', data_type=FieldType.text),
            Field('LAND_RANK', data_type=FieldType.mediumint),
            Field('LETTER', data_type=FieldType.text),
            Field('FIRST_LETTER', data_type=FieldType.text),
            Field('ISO_SUB_NO', data_type=FieldType.mediumint),
            Field('MAX_ISO_SUB_NO', data_type=FieldType.mediumint),
        ]
    # End _get_fields method

    def test_context(self, inputs, mem_gpkg):
        """
        Test context manager
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        with QueryDissolve(source, target=target, fields=[name, continent],
                           statistics=[stat], as_multi_part=True,
                           xy_tolerance=None) as query:
            with query.source.geopackage.connection as cin:
                assert query.group_count == 212
                cursor = cin.execute(query.select)
                records = cursor.fetchall()
                assert len(records) == 212
        with QueryDissolve(source, target=target, fields=[continent],
                           statistics=[stat], as_multi_part=True,
                           xy_tolerance=None) as query:
            with query.source.geopackage.connection as cin:
                assert query.group_count == 2
                cursor = cin.execute(query.select)
                records = cursor.fetchall()
                assert len(records) == 2
                ids, names, medians = zip(*records)
                assert ids == (1, 2)
                assert names == ('EAST', 'WEST')
                assert medians == (115.5, 99)
    # End test_context method

    def test_select(self, inputs, mem_gpkg):
        """
        Test Select
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        query = QueryDissolve(
            source, target=target, fields=[name, continent],
            statistics=[stat], as_multi_part=True,
            xy_tolerance=None)
        sql = query.select
        assert 'SELECT __DRID__, NAME, CONTINENT, spyops_median(ISO_SUB_NO)' in sql
        assert 'SELECT dense_rank() OVER (' in sql
        assert 'ORDER BY NAME, CONTINENT) AS __DRID__, NAME, CONTINENT, ISO_SUB_NO' in sql
        assert 'GROUP BY __DRID__' in sql
    # End test_select method

    def test_select_geometry(self, inputs, mem_gpkg):
        """
        Test Select Geometry
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        query = QueryDissolve(
            source, target=target, fields=[name, continent],
            statistics=[stat], as_multi_part=True,
            xy_tolerance=None)
        sql = query.select_geometry
        assert 'SELECT *' in sql
        assert 'SELECT geom "[Polygon]", dense_rank() OVER (' in sql
        assert 'ORDER BY NAME, CONTINENT) AS __DRID__'
        assert 'FROM dissolve_si_a' in sql
        assert 'WHERE __DRID__ BETWEEN' in sql
    # End test_select_geometry method

    def test_insert(self, inputs, mem_gpkg):
        """
        Test Insert
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        query = QueryDissolve(
            source, target=target, fields=[name, continent],
            statistics=[stat], as_multi_part=True,
            xy_tolerance=None)
        sql = query.insert
        assert 'INTO dis_a(SHAPE, NAME, CONTINENT, MEDIAN_ISO_SUB_NO)' in sql
        assert 'VALUES (?, ?, ?, ?)' in sql
    # End test_insert method

    def test_field_names_and_count(self, inputs, mem_gpkg):
        """
        Test field names and count
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        query = QueryDissolve(
            source, target=target, fields=[name, continent],
            statistics=[stat], as_multi_part=True,
            xy_tolerance=None)
        count, insert_names, select_names = query._field_names_and_count(source)
        assert count == 4
        assert insert_names == 'geom, NAME, CONTINENT, MEDIAN_ISO_SUB_NO'
        assert select_names == '__DRID__, NAME, CONTINENT, spyops_median(ISO_SUB_NO)'
    # End test_field_names_and_count method

    def test_get_unique_fields(self, inputs, mem_gpkg):
        """
        Test get unique fields
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        query = QueryDissolve(
            source, target=target, fields=[name, continent],
            statistics=[stat], as_multi_part=True,
            xy_tolerance=None)
        fields = query._get_unique_fields()
        assert len(fields) == 3
        assert [f.name for f in fields] == ['NAME', 'CONTINENT', 'MEDIAN_ISO_SUB_NO']
    # End test_get_unique_fields method

    def test_statistics(self, inputs, mem_gpkg):
        """
        Test statistics
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        query = QueryDissolve(
            source, target=target, fields=[name, continent],
            statistics=[stat, stat], as_multi_part=True,
            xy_tolerance=None)
        assert len(query._statistics) == 2
        assert len(query.statistics) == 1
    # End test_statistics method

    @mark.parametrize('name, as_multi_part, expected', [
        ('admin_a', True, 'MULTIPOLYGON'),
        ('admin_a', False, 'POLYGON'),
        ('admin_mp_a', True, 'MULTIPOLYGON'),
        ('admin_mp_a', False, 'POLYGON'),
    ])
    def test_get_target_shape_type(self, world_features, mem_gpkg, name, as_multi_part, expected):
        """
        Test get target shape type
        """
        source = world_features[name]
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        query = QueryDissolve(
            source, target=target, fields=[name, continent],
            statistics=[stat], as_multi_part=as_multi_part,
            xy_tolerance=None)
        assert query._get_target_shape_type() == expected
    # End test_get_target_shape_type method

    def test_dissolved_geometries(self, inputs, mem_gpkg):
        """
        Test dissolved geometries
        """
        source = inputs['dissolve_si_a']
        target = FeatureClass(geopackage=mem_gpkg, name='dis_a')
        name, _, _, _, _, _, continent, _, _, _, sub_no, _ = self._get_fields()
        stat = Median(sub_no)
        with QueryDissolve(source, target=target, fields=[name, continent],
                           statistics=[stat], as_multi_part=True,
                           xy_tolerance=None) as query:
            gen = query.dissolved_geometries()
            geoms = next(gen)
            assert len(geoms) == 212
        with QueryDissolve(source, target=target, fields=[continent],
                           statistics=[stat], as_multi_part=True,
                           xy_tolerance=None) as query:
            gen = query.dissolved_geometries()
            geoms = next(gen)
            assert len(geoms) == 2
    # End test_dissolved_geometries method
# End TestQueryDissolve class


if __name__ == '__main__':  # pragma: no cover
    pass
