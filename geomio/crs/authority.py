# -*- coding: utf-8 -*-
"""
Base classes for Coordinate Reference System (CRS) components
"""


from typing import Self

from pyproj import CRS

from geomio.shared.constant import (
    AUTHORITY_KEY, CODE_KEY, COLON, CUSTOM_UPPER, EMPTY, EPSG, ESRI, ID_KEY,
    NONE, PLUS, UNKNOWN, ZERO_STR)


def authorities() -> set[str]:
    """
    Authorities
    """
    return {EPSG, ESRI}
# End authorities function


class Authority:
    """
    Authority
    """
    def __init__(self, names: str | tuple[str, ...],
                 codes: str | tuple[str, ...], crs: CRS | None = None) -> None:
        """
        Initialize the Authority class
        """
        super().__init__()
        # NOTE never more than two codes at most, enforce via slice
        self._names: tuple[str, ...] = self._make_tuple(names, CUSTOM_UPPER)[:2]
        self._codes: tuple[str, ...] = self._make_tuple(codes, ZERO_STR)[:2]
        self._crs: CRS | None = crs
    # End init built-in

    def __eq__(self, other: Self) -> bool:
        """
        Equals Override
        """
        if not isinstance(other, self.__class__):
            return False
        if not self._compare_strings(self.names, other.names):
            return False
        return self._compare_strings(self.codes, other.codes)
    # End eq built-in

    def __hash__(self) -> int:
        """
        Hash Override
        """
        return hash((self._bulk_lower(self.names),
                     self._bulk_lower(self.codes)))
    # End hash built-in

    def __repr__(self) -> str:
        """
        Representation Override
        """
        if self._crs:
            return (f'Authority(names={self._names!r}, codes={self._codes!r}, '
                    f'crs={self._crs!r})')
        return f'Authority(names={self._names!r}, codes={self._codes!r})'
    # End repr built-in

    def _compare_strings(self, from_values: tuple[str, ...],
                         to_values: tuple[str, ...]) -> bool:
        """
        Compare Stings Case insensitive
        """
        return self._bulk_lower(from_values) == self._bulk_lower(to_values)
    # End _compare_strings method

    @staticmethod
    def _bulk_lower(values: tuple[str, ...]) -> tuple[str, ...]:
        """
        Bulk Lower
        """
        return tuple([v.casefold() for v in values])
    # End _bulk_lower method

    @property
    def names(self) -> tuple[str, ...]:
        """
        Names
        """
        return self._names
    # End names property

    @property
    def codes(self) -> tuple[str, ...]:
        """
        Codes
        """
        return self._codes
    # End codes property

    @staticmethod
    def _make_tuple(values: str | tuple[str, ...], default: str) -> tuple[str, ...]:
        """
        Make Tuple
        """
        if not values:
            return default,
        if isinstance(values, (str, int, float)):
            return str(values),
        return tuple(str(v or default) for v in values)
    # End _make_tuple method

    def pretty_name_and_code(self) -> tuple[str, str]:
        """
        Pretty Name and Code, avoid repeating name but retain all codes.
        """
        names = []
        for name in self.names:
            if name in names:
                continue
            names.append(name)
        return PLUS.join(names), PLUS.join(self.codes)
    # End pretty_name_and_code method

    def org_name_and_code(self) -> tuple[str, str]:
        """
        Organization Name and Code for use with Geopackage Spatial Reference,
        must be a single organization name and a single code value since it
        has to be stored in the database for organization name and id.
        """
        if len(set(self.names)) != 1 or len(set(self.codes)) != 1:
            return CUSTOM_UPPER, ZERO_STR
        name, *_ = self.names
        code, *_ = self.codes
        return name, code
    # End org_name_and_code method

    def as_label(self, braces: bool = False) -> str:
        """
        Make Label
        """
        auth_name, auth_code = self.pretty_name_and_code()
        has_bad_name = CUSTOM_UPPER in self.names or NONE in self.names
        has_bad_code = ZERO_STR in self.codes or NONE in self.codes
        if has_bad_name and has_bad_code:
            name = self._crs.name
            if name.casefold() == UNKNOWN.casefold():
                auth_name = CUSTOM_UPPER
                auth_code = EMPTY
            else:
                auth_name = CUSTOM_UPPER
                auth_code = name
        return self.make_authority_label(
            auth_name=auth_name, auth_code=auth_code, braces=braces)
    # End as_label method

    @staticmethod
    def make_authority_label(auth_name: str, auth_code: str | int | None,
                             braces: bool = False) -> str:
        """
        Make Authority Label
        """
        if not auth_code:
            text = f'{auth_name}'
        elif (auth_name in (CUSTOM_UPPER, NONE) and
              auth_code not in (ZERO_STR, NONE, EMPTY)):
            text = f'{CUSTOM_UPPER}{COLON}{auth_code}'
        elif (auth_name not in (CUSTOM_UPPER, NONE) and
              auth_code not in (ZERO_STR, NONE, EMPTY)):
            text = f'{auth_name}{COLON}{auth_code}'
        else:
            text = f'{auth_name}'
        if not braces:
            return text
        return f'[{text}]'
    # End make_authority_label method

    @property
    def has_single_code(self) -> bool:
        """
        Can the CRS be described using a single code (built-in or custom)
        """
        return len(self.codes) == 1
    # End has_single_code property

    @property
    def is_valid(self) -> bool:
        """
        Is Valid
        """
        return NONE not in self.names
    # End is_valid property

    @classmethod
    def from_crs(cls, crs: CRS) -> 'Authority':
        """
        Build the Authority from a CRS object internals
        """
        if not crs.srs:
            return Authority(names=NONE, codes=NONE, crs=crs)
        if authority := _from_json(crs):
            return authority
        if crs.is_compound:
            crs_list = crs.sub_crs_list
        else:
            crs_list = [crs]
        names = []
        codes = []
        for sub in crs_list:
            if authority := to_authority(sub):
                names.extend(authority.names)
                codes.extend(authority.codes)
            else:
                names.append(EMPTY)
                codes.append(EMPTY)
        names, codes = tuple(names), tuple(codes)
        return cls(names=names, codes=codes, crs=crs)
    # End from_crs method
# End Authority class


def _from_json(crs: CRS) -> Authority | None:
    """
    From JSON dictionary of the CRS object
    """
    if not (auth_info := crs.to_json_dict().get(ID_KEY, {})):
        return None
    auth_name = auth_info.get(AUTHORITY_KEY)
    auth_code = auth_info.get(CODE_KEY)
    if auth_name and auth_code:
        return Authority(names=auth_name, codes=auth_code, crs=crs)
    return None
# End _from_json method


def to_authority(crs: CRS, min_confidence: int = 100) -> Authority | None:
    """
    Light wrapper to allow for easy inline use, begin by looking at the JSON
    dictionary for authority identification, fail over to using to_authority
    method with 100% confidence (default) and specifying the authority name.
    """
    if authority := _from_json(crs):
        return authority
    for auth_name in authorities():
        if result := crs.to_authority(
                auth_name=auth_name, min_confidence=min_confidence):
            return Authority(*result, crs=crs)
    return None
# End to_authority method


if __name__ == '__main__':  # pragma: no cover
    pass
