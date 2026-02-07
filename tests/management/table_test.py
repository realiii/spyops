# -*- coding: utf-8 -*-
"""
Tests for Table Module
"""


from pytest import mark

from spyops.management import get_count


pytestmark = [mark.management, mark.table]


def test_get_count(ntdb_zm):
    """
    Test get count
    """
    source = ntdb_zm['hydro_a']
    result = get_count(source)
    assert result == 12_950
# End test_get_count function


if __name__ == '__main__':  # pragma: no cover
    pass
