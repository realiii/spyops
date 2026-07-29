# -*- coding: utf-8 -*-
"""
Tests for Delimited File Conversion
"""


from pytest import mark

from spyops.conversion import table_to_delimited_file
from spyops.shared.constant import COMMA, PIPE
from spyops.shared.sort import Descending

pytestmark = [mark.conversion, mark.delimited]


class TestTableToDelimitedFile:
    """
    Test Table to Delimited File
    """
    @mark.parametrize('fc_name, approx_size', [
        ('gps_p', 273_000),
        ('gps_lcc_p', 273_000),
        ('gps_mp', 1500),
        ('gps_l', 1100),
        ('gps_lcc_l', 1100),
        ('gps_ml', 800),
    ])
    @mark.parametrize('delimiter', [
        COMMA,
        PIPE,
    ])
    @mark.parametrize('use_aliases', [
        True,
        False,
    ])
    def test_table_to_delimited_file(self, inputs, tmp_path, fc_name,
                                     approx_size, delimiter, use_aliases):
        """
        Test table to delimited file
        """
        fc = inputs[fc_name]
        path = tmp_path.joinpath(fc_name).with_suffix('.csv')
        output = table_to_delimited_file(
            fc, target=path, delimiter=delimiter, use_aliases=use_aliases,
            where_clause="""fid > 2""", sort_fields=Descending('fid'))
        assert output.is_file()
        assert output.stat().st_size > approx_size
    # End test_table_to_delimited_file method
# End TestTableToDelimitedFile class


if __name__ == '__main__':  # pragma: no cover
    pass
