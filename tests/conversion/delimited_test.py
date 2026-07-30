# -*- coding: utf-8 -*-
"""
Tests for Delimited File Conversion
"""


from fudgeo import Table
from pytest import mark

from spyops.conversion import delimited_file_to_table, table_to_delimited_file
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
    def test_function(self, inputs, tmp_path, fc_name,
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
    # End test_function method
# End TestTableToDelimitedFile class


class TestDelimitedFileToTable:
    """
    Test Delimited File to Table
    """
    @mark.parametrize('name, delimiter, count', [
        ('badname.csv', COMMA, 7),
        ('comma.csv', COMMA, 7),
        ('empty_columns.csv', COMMA, 7),
        ('good.csv', COMMA, 7),
        ('header_data_mismatch.csv', COMMA, 139),
        ('keywords.csv', COMMA, 7),
        ('lower.csv', COMMA, 7),
        ('missingdata.csv', COMMA, 7),
        ('missingheader.csv', COMMA, 6),
        ('missingname.csv', COMMA, 7),
        ('nodata.csv', COMMA, 0),
        ('null.csv', COMMA, 7),
        ('null_as_string.csv', COMMA, 7),
        ('pipe.csv', PIPE, 7),
        ('poly.csv', COMMA, 7),
        ('repeated_column.csv', COMMA, 7),
    ])
    def test_function(self, mem_gpkg, csv_path, name, delimiter, count):
        """
        Test delimited file to table
        """
        path = csv_path.joinpath(name)
        assert path.is_file()
        target = Table(mem_gpkg, name='csv_load')
        tbl = delimited_file_to_table(
            path, target=target, delimiter=delimiter)
        assert len(tbl) == count
    # End test_function method
# End TestDelimitedFileToTable class


if __name__ == '__main__':  # pragma: no cover
    pass
