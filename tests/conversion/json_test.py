# -*- coding: utf-8 -*-
"""
Tests for JSON Conversion
"""


from json import load

from fudgeo import FeatureClass
from pytest import mark

from spyops.conversion import features_to_geojson, geojson_to_features
from spyops.shared.keywords import CRS_KEY, FEATURES_KEY, HASM_KEY, HASZ_KEY


pytestmark = [mark.conversion, mark.json]


class TestFeaturesToGeoJSON:
    """
    Test Features to GeoJSON
    """
    @mark.parametrize('as_wgs84', [
        True,
        False
    ])
    @mark.parametrize('formatted', [
        True,
        False
    ])
    @mark.parametrize('include_z', [
        True,
        False
    ])
    @mark.parametrize('include_m', [
        True,
        False
    ])
    @mark.parametrize('use_aliases', [
        True,
        False
    ])
    def test_options(self, inputs, tmp_path, as_wgs84, formatted, include_z, include_m, use_aliases):
        """
        Test options
        """
        source = inputs['clipper_a']
        target = tmp_path / 'clipper_a.geojson'
        path = features_to_geojson(
            source, target, as_wgs84=as_wgs84, formatted=formatted,
            include_z=include_z, include_m=include_m,
            use_aliases=use_aliases)
        assert path.is_file()
    # End test_options method

    @mark.zm
    @mark.parametrize('as_wgs84', [
        True,
        False
    ])
    @mark.parametrize('include_z', [
        True,
        False
    ])
    @mark.parametrize('include_m', [
        True,
        False
    ])
    def test_zm(self, ntdb_zm_small, tmp_path, as_wgs84, include_z, include_m):
        """
        Test polygon with ZM
        """
        source = ntdb_zm_small['hydro_6654_zm_a']
        target = tmp_path / 'hydro_6654_zm_a.geojson'
        path = features_to_geojson(
            source, target, as_wgs84=as_wgs84,
            include_z=include_z, include_m=include_m)
        assert path.is_file()
        data = load(path.open())
        if not as_wgs84:
            assert CRS_KEY in data
        else:
            assert CRS_KEY not in data
        if include_z:
            assert HASZ_KEY in data
        else:
            assert HASZ_KEY not in data
        if include_m:
            assert HASM_KEY in data
        else:
            assert HASM_KEY not in data
    # End test_zm method

    @mark.parametrize('name', [
        'structures_10tm_m_a',
        'structures_10tm_m_ma',
        'toponymy_10tm_m_p',
        'toponymy_10tm_m_mp',
        'transmission_10tm_zm_l',
        'transmission_10tm_zm_ml',
    ])
    @mark.parametrize('as_wgs84', [
        True,
        False
    ])
    def test_geometry_types(self, ntdb_zm_small, tmp_path, name, as_wgs84):
        """
        Test geometry types
        """
        source = ntdb_zm_small[name]
        target = tmp_path / f'{name}.geojson'
        path = features_to_geojson(source, target, as_wgs84=as_wgs84)
        assert path.is_file()
        data = load(path.open())
        assert len(data[FEATURES_KEY]) == len(source)
        assert HASZ_KEY not in data
        assert HASM_KEY not in data
        if not as_wgs84:
            assert CRS_KEY in data
        else:
            assert CRS_KEY not in data
    # End test_geometry_types method
# End TestFeaturesToGeoJSON class


class TestGeoJSONToFeatures:
    """
    Test GeoJSON to Features
    """
    @mark.parametrize('name, count, srs_id', [
        ('point.geojson', 11, 4617),
        ('point_alias_formatted.geojson', 11, 4617),
        ('point_formatted.geojson', 11, 4617),
        ('point_wgs84.geojson', 11, 4326),
        ('point_wgs84_formatted.geojson', 11, 4326),
        ('point_zm.geojson', 11, 4617),
        ('point_zm_formatted.geojson', 11, 4617),
        ('point_zm_wgs84.geojson', 11, 4326),
        ('point_zm_wgs84_formatted.geojson', 11, 4326),
        ('line_formatted.geojson', 66, 2955),
        ('line_wgs84_formatted.geojson', 66, 4326),
        ('line_zm.geojson', 66, 2955),
        ('line_zm_formatted.geojson', 66, 2955),
        ('line_zm_wgs84_formatted.geojson', 66, 4326),
        ('polygon.geojson', 382, 4617),
        ('polygon_wgs84.geojson', 382, 4326),
        ('polygon_wgs84_formatted.geojson', 382, 4326),
        ('polygon_zm_formatted.geojson', 382, 4617),
        ('polygon_zm_wgs84_formatted.geojson', 382, 4326),
        ('multipoint_formatted.geojson', 1, 2955),
        ('multipoint_wgs84.geojson', 1, 4326),
        ('multipoint_wgs84_formatted.geojson', 1, 4326),
        ('multipoint_zm.geojson', 1, 2955),
        ('multipoint_zm_formatted.geojson', 1, 2955),
        ('multipoint_zm_wgs84.geojson', 1, 4326),
        ('multipoint_zm_wgs84_formatted.geojson', 1, 4326),
        ('multiline.geojson', 4, 4617),
        ('multiline_formatted.geojson', 4, 4617),
        ('multiline_wgs84.geojson', 4, 4326),
        ('multiline_wgs84_formatted.geojson', 4, 4326),
        ('multipolygon.geojson', 18, 102179),
        ('multipolygon_formatted.geojson', 18, 102179),
        ('multipolygon_wgs84.geojson', 18, 4326),
        ('multipolygon_wgs84_formatted.geojson', 18, 4326),
        ('multipolygon_zm.geojson', 18, 102179),
        ('multipolygon_zm_formatted.geojson', 18, 102179),
        ('multipolygon_zm_wgs84.geojson', 18, 4326),
        ('multipolygon_zm_wgs84_formatted.geojson', 18, 4326),
    ])
    def test_function(self, mem_gpkg, geojson_path, name, count, srs_id):
        """
        Test function
        """
        source = geojson_path.joinpath(name)
        assert source.is_file()
        target = FeatureClass(mem_gpkg, name=source.stem)
        result = geojson_to_features(source, target=target)
        assert result.spatial_reference_system.srs_id == srs_id
        assert len(result) == count
    # End test_function method
# End TestGeoJSONToFeatures class


if __name__ == '__main__':  # pragma: no cover
    pass
