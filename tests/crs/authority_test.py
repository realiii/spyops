# -*- coding: utf-8 -*-
"""
Tests for Authority class and related functions
"""


from pyproj import CRS
from pytest import mark

from constants import (
    CUSTOM_PROJ_STR, CUSTOM_CAMACUPA_UTM_32S, CUSTOM_COMPOUND_AUTH,
    CUSTOM_COMPOUND_NO_AUTH_HORIZ, CUSTOM_COMPOUND_NO_AUTH_VERT,
    CUSTOM_THIRD_PARTY_AUTHORITY,  COMPOUND_ESRI_EPSG_MIX)
from geomio.crs.authority import Authority, authorities
from geomio.crs.util import _get_crs_component, get_crs_authority
from geomio.shared.constant import CUSTOM_UPPER, EPSG, ESRI
from geomio.shared.enumeration import InfoOption

pytestmark = [mark.crs]


def test_authorities():
    """
    Test authorities
    """
    assert authorities() == {EPSG, ESRI}
# End test_authorities function


def test_authority_repr():
    """
    Test Authority Representation
    """
    assert repr(Authority(EPSG, '4326')) == "Authority(names=('EPSG',), codes=('4326',))"
# End test_authority_repr function


@mark.parametrize('crs, option, names_codes, label, pretty, org', [
    (CRS(2962), InfoOption.ORIGINAL, (EPSG, '2962'), 'EPSG:2962', (EPSG, '2962'), (EPSG, '2962')),
    (CRS(2962), InfoOption.HORIZONTAL, (EPSG, '2962'), 'EPSG:2962', (EPSG, '2962'), (EPSG, '2962')),
    (CRS(2962), InfoOption.VERTICAL, (EPSG, '2962'), 'EPSG:2962', (EPSG, '2962'), (EPSG, '2962')),
    (CRS(4326), InfoOption.ORIGINAL, (EPSG, '4326'), 'EPSG:4326', (EPSG, '4326'), (EPSG, '4326')),
    (CRS(4326), InfoOption.HORIZONTAL, (EPSG, '4326'), 'EPSG:4326', (EPSG, '4326'), (EPSG, '4326')),
    (CRS(4326), InfoOption.VERTICAL, (EPSG, '4326'), 'EPSG:4326', (EPSG, '4326'), (EPSG, '4326')),
    (CRS(8780), InfoOption.ORIGINAL, (EPSG, '8780'), 'EPSG:8780', (EPSG, '8780'), (EPSG, '8780')),
    (CRS(8780), InfoOption.HORIZONTAL, (EPSG, '2276'), 'EPSG:2276', (EPSG, '2276'), (EPSG, '2276')),
    (CRS(8780), InfoOption.VERTICAL, (EPSG, '6360'), 'EPSG:6360', (EPSG, '6360'), (EPSG, '6360')),
    (CRS(8730), InfoOption.ORIGINAL, (EPSG, '8730'), 'EPSG:8730', (EPSG, '8730'), (EPSG, '8730')),
    (CRS(8730), InfoOption.HORIZONTAL, (EPSG, '2241'), 'EPSG:2241', (EPSG, '2241'), (EPSG, '2241')),
    (CRS(8730), InfoOption.VERTICAL, (EPSG, '6360'), 'EPSG:6360', (EPSG, '6360'), (EPSG, '6360')),
    (CRS(CUSTOM_PROJ_STR), InfoOption.ORIGINAL, (CUSTOM_UPPER, '0'), CUSTOM_UPPER, (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_PROJ_STR), InfoOption.HORIZONTAL, (CUSTOM_UPPER, '0'), CUSTOM_UPPER, (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_PROJ_STR), InfoOption.VERTICAL, (CUSTOM_UPPER, '0'), CUSTOM_UPPER, (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_CAMACUPA_UTM_32S), InfoOption.ORIGINAL, (CUSTOM_UPPER, '0'), 'CUSTOM:Camacupa UTM 32s custom', (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_CAMACUPA_UTM_32S), InfoOption.HORIZONTAL, (CUSTOM_UPPER, '0'), 'CUSTOM:Camacupa UTM 32s custom', (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_CAMACUPA_UTM_32S), InfoOption.VERTICAL, (CUSTOM_UPPER, '0'), 'CUSTOM:Camacupa UTM 32s custom', (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_COMPOUND_AUTH), InfoOption.ORIGINAL, ((EPSG, EPSG), ('26912', '6360')), 'EPSG:26912+6360', (EPSG, '26912+6360'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_COMPOUND_AUTH), InfoOption.HORIZONTAL, (EPSG, '26912'), 'EPSG:26912', (EPSG, '26912'), (EPSG, '26912')),
    (CRS(CUSTOM_COMPOUND_AUTH), InfoOption.VERTICAL, (EPSG, '6360'), 'EPSG:6360', (EPSG, '6360'), (EPSG, '6360')),
    (CRS(CUSTOM_COMPOUND_NO_AUTH_HORIZ), InfoOption.ORIGINAL, ((CUSTOM_UPPER, EPSG), ('0', '6360')), 'CUSTOM:Camacupa_UTM_32s_custom + NAVD88 height (ftUS)', ('CUSTOM+EPSG', '0+6360'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_COMPOUND_NO_AUTH_HORIZ), InfoOption.HORIZONTAL, (CUSTOM_UPPER, '0'), 'CUSTOM:Camacupa_UTM_32s_custom', (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_COMPOUND_NO_AUTH_HORIZ), InfoOption.VERTICAL, (EPSG, '6360'), 'EPSG:6360', (EPSG, '6360'), (EPSG, '6360')),
    (CRS(CUSTOM_COMPOUND_NO_AUTH_VERT), InfoOption.ORIGINAL, ((EPSG, CUSTOM_UPPER), ('26912', '0')), 'CUSTOM:NAD83 / UTM zone 12N + Jimmy-O', ('EPSG+CUSTOM', '26912+0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_COMPOUND_NO_AUTH_VERT), InfoOption.HORIZONTAL, (EPSG, '26912'), 'EPSG:26912', (EPSG, '26912'), (EPSG, '26912')),
    (CRS(CUSTOM_COMPOUND_NO_AUTH_VERT), InfoOption.VERTICAL, (CUSTOM_UPPER, '0'), 'CUSTOM:Jimmy-O', (CUSTOM_UPPER, '0'), (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_THIRD_PARTY_AUTHORITY), InfoOption.ORIGINAL, ('ThirdParty', '54051'), 'ThirdParty:54051', ('ThirdParty', '54051'), ('ThirdParty', '54051')),
    (CRS(CUSTOM_THIRD_PARTY_AUTHORITY), InfoOption.HORIZONTAL, ('ThirdParty', '54051'), 'ThirdParty:54051', ('ThirdParty', '54051'), ('ThirdParty', '54051')),
    (CRS(CUSTOM_THIRD_PARTY_AUTHORITY), InfoOption.VERTICAL, ('ThirdParty', '54051'), 'ThirdParty:54051', ('ThirdParty', '54051'), ('ThirdParty', '54051')),
    (CRS.from_authority(ESRI, 102579), InfoOption.ORIGINAL, (ESRI, '102579'), 'ESRI:102579', (ESRI, '102579'), (ESRI, '102579')),
    (CRS.from_authority(ESRI, 102579), InfoOption.HORIZONTAL, (ESRI, '102579'), 'ESRI:102579', (ESRI, '102579'), (ESRI, '102579')),
    (CRS.from_authority(ESRI, 102579), InfoOption.VERTICAL, (ESRI, '102579'), 'ESRI:102579', (ESRI, '102579'), (ESRI, '102579')),
    (CRS.from_wkt(COMPOUND_ESRI_EPSG_MIX), InfoOption.ORIGINAL, ((ESRI, EPSG), ('102190', '6357')), 'ESRI+EPSG:102190+6357', ('ESRI+EPSG', '102190+6357'), (CUSTOM_UPPER, '0')),
    (CRS.from_wkt(COMPOUND_ESRI_EPSG_MIX), InfoOption.HORIZONTAL, (ESRI, '102190'), 'ESRI:102190', (ESRI, '102190'), (ESRI, '102190')),
    (CRS.from_wkt(COMPOUND_ESRI_EPSG_MIX), InfoOption.VERTICAL, (EPSG, '6357'), 'EPSG:6357', (EPSG, '6357'), (EPSG, '6357')),
])
def test_get_crs_authority(crs, option, names_codes, label, pretty, org):
    """
    Test getting CRS info safely via get_crs_authority
    """
    auth = Authority(*names_codes, crs=crs)
    authority = get_crs_authority(crs, option=option)
    assert isinstance(authority, Authority)
    assert authority != 123
    assert authority == auth
    assert authority.is_valid
    is_single = isinstance(names_codes[0], str)
    assert authority.has_single_code is is_single
    assert authority.as_label() == label
    assert authority.as_label(True) == f'[{label}]'
    assert authority.pretty_name_and_code() == pretty
    assert authority.org_name_and_code() == org
# End test_get_crs_authority function


@mark.parametrize('crs, option, names_codes', [
    (CRS(4326), InfoOption.ORIGINAL, (EPSG, '4326')),
    (CRS(4326), InfoOption.HORIZONTAL, (EPSG, '4326')),
    (CRS(4326), InfoOption.VERTICAL, (EPSG, '4326')),
    (CRS(8780), InfoOption.ORIGINAL, (EPSG, '8780')),
    (CRS(8780), InfoOption.HORIZONTAL, (EPSG, '2276')),
    (CRS(8780), InfoOption.VERTICAL, (EPSG, '6360')),
    (CRS(8730), InfoOption.ORIGINAL, (EPSG, '8730')),
    (CRS(8730), InfoOption.HORIZONTAL, (EPSG, '2241')),
    (CRS(8730), InfoOption.VERTICAL, (EPSG, '6360')),
    (CRS(CUSTOM_PROJ_STR), InfoOption.ORIGINAL, (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_PROJ_STR), InfoOption.HORIZONTAL, (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_PROJ_STR), InfoOption.VERTICAL, (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_CAMACUPA_UTM_32S), InfoOption.ORIGINAL, (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_CAMACUPA_UTM_32S), InfoOption.HORIZONTAL, (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_CAMACUPA_UTM_32S), InfoOption.VERTICAL, (CUSTOM_UPPER, '0')),
    (CRS(CUSTOM_COMPOUND_AUTH), InfoOption.ORIGINAL, ((EPSG, EPSG), ('26912', '6360'))),
    (CRS(CUSTOM_COMPOUND_AUTH), InfoOption.HORIZONTAL, (EPSG, '26912')),
    (CRS(CUSTOM_COMPOUND_AUTH), InfoOption.VERTICAL, (EPSG, '6360')),
    (CRS(CUSTOM_THIRD_PARTY_AUTHORITY), InfoOption.ORIGINAL, ('ThirdParty', '54051')),
    (CRS(CUSTOM_THIRD_PARTY_AUTHORITY), InfoOption.HORIZONTAL, ('ThirdParty', '54051')),
    (CRS(CUSTOM_THIRD_PARTY_AUTHORITY), InfoOption.VERTICAL, ('ThirdParty', '54051')),
    (CRS(COMPOUND_ESRI_EPSG_MIX), InfoOption.ORIGINAL, ((ESRI, EPSG), ('102190', '6357'))),
    (CRS(COMPOUND_ESRI_EPSG_MIX), InfoOption.HORIZONTAL, (ESRI, '102190')),
    (CRS(COMPOUND_ESRI_EPSG_MIX), InfoOption.VERTICAL, (EPSG, '6357')),
    (CRS.from_authority(ESRI, 102579), InfoOption.ORIGINAL, (ESRI, '102579')),
    (CRS.from_authority(ESRI, 102579), InfoOption.HORIZONTAL, (ESRI, '102579')),
    (CRS.from_authority(ESRI, 102579), InfoOption.VERTICAL, (ESRI, '102579')),
])
def test_authority_from_crs(crs, option, names_codes):
    """
    Test getting CRS info safely via from_crs
    """
    if option == InfoOption.HORIZONTAL:
        crs = _get_crs_component(crs, use_horizontal=True)
    elif option == InfoOption.VERTICAL:
        crs = _get_crs_component(crs, use_horizontal=False)
    auth = Authority(*names_codes, crs=crs)
    authority = Authority.from_crs(crs)
    assert authority == auth
# End test_authority_from_crs function


if __name__ == '__main__':  # pragma: no cover
    pass
