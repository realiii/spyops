# -*- coding: utf-8 -*-
"""
Tests for GPS Conversion
"""


from pytest import mark

from spyops.conversion.gps import features_to_gpx

pytestmark = [mark.conversion, mark.gps]


class TestFeaturesToGPX:
    """
    Test Features to GPX
    """
    @mark.parametrize('fc_name, approx_size', [
        ('gps_p', 157_000),
        ('gps_lcc_p', 157_000),
        ('gps_mp', 157_000),
        ('gps_l', 65_000),
        ('gps_lcc_l', 65_000),
        ('gps_ml', 65_000),
    ])
    def test_sans_attr(self, inputs, tmp_path, fc_name, approx_size):
        """
        Test sans attributes
        """
        fc = inputs[fc_name]
        path = tmp_path.joinpath(fc_name)
        output = features_to_gpx(fc, target=path)
        assert output.is_file()
        assert output.stat().st_size > approx_size
    # End test_sans_attr method

    @mark.parametrize('fc_name, fields, approx_size', [
        ('gps_p', ('name', 'system', 'distance', 'dt'), 464_000),
        ('gps_lcc_p', ('name', 'system', 'distance', 'dt'), 464_000),
        ('gps_mp', ('name', 'first_system', 'avg_distance', None), 361_000),
        ('gps_l', ('name', 'system', 'depth', 'day'), 129_000),
        ('gps_lcc_l', ('name', 'system', 'depth', 'day'), 129_000),
        ('gps_ml', ('name', 'first_system', 'avg_depth', 'first_day'), 129_000),
    ])
    def test_with_attr(self, inputs, tmp_path, fc_name, fields, approx_size):
        """
        Test with attributes
        """
        fc = inputs[fc_name]
        path = tmp_path.joinpath(fc_name)
        name, description, elevation, date = fields
        output = features_to_gpx(
            fc, target=path, name_field=name, description_field=description,
            z_field=elevation, date_field=date)
        assert output.is_file()
        assert output.stat().st_size > approx_size
    # End test_with_attr method
# End TestFeaturesToGPX class


if __name__ == '__main__':  # pragma: no cover
    pass
