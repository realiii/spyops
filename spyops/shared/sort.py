# -*- coding: utf-8 -*-
"""
Sort Fields
"""


from abc import ABCMeta, abstractmethod
from typing import Self

from fudgeo import Field

from spyops.shared.enumeration import SortOrder


class AbstractSortField(metaclass=ABCMeta):
    """
    Abstract Sort Field
    """
    def __init__(self, field: Field | str) -> None:
        """
        Initialize the AbstractSortField class
        """
        super().__init__()
        self._field: Field | str = field
    # End init built-in

    def __eq__(self, other: Self) -> bool:
        """
        Equals Override
        """
        if not isinstance(other, self.__class__):  # pragma: no cover
            return NotImplemented
        return self.field == other.field and self.sort_order == other.sort_order
    # End eq built-in

    def __hash__(self) -> int:
        """
        Hash Implementation
        """
        return hash((self.field, self.sort_order))
    # End hash built-in

    def __repr__(self) -> str:
        """
        Representation Override
        """
        # noinspection PyUnresolvedReferences
        name = self.field.escaped_name
        if self.sort_order == SortOrder.DESCENDING:
            return f'{name} DESC'
        return f'{name} ASC'
    # End repr built-in

    def validate(self) -> None:
        """
        Validate
        """
        if not isinstance(self.field, Field):
            raise TypeError('Expected field to be a Field object')
    # End validate method

    @property
    def field(self) -> Field | str:
        """
        Field
        """
        return self._field

    @field.setter
    def field(self, value: Field) -> None:
        if not isinstance(value, Field):
            return
        self._field = value
    # End field property

    @property
    @abstractmethod
    def sort_order(self) -> SortOrder:
        """
        Sort Order
        """
        pass
    # End sort_order property
# End AbstractSortField class


class Ascending(AbstractSortField):
    """
    Ascending Sort Field
    """
    @property
    def sort_order(self) -> SortOrder:
        """
        Sort Order
        """
        return SortOrder.ASCENDING
    # End sort_order property
# End Ascending class


class Descending(AbstractSortField):
    """
    Descending Sort Field
    """
    @property
    def sort_order(self) -> SortOrder:
        """
        Sort Order
        """
        return SortOrder.DESCENDING
    # End sort_order property
# End Descending class


if __name__ == '__main__':  # pragma: no cover
    pass
