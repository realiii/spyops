# -*- coding: utf-8 -*-
"""
Utility functions for testing
"""


from os.path import pathsep
from pathlib import Path

from pyproj.datadir import append_data_dir, get_data_dir, set_data_dir


GRID_DIR: Path = Path(__file__).parent.parent / 'grids'


def use_grids(flag: bool) -> None:
    """
    Uses sync'd local grids in tests for transforms or disables them
    """
    if flag:
        append_data_dir(str(GRID_DIR))
    else:
        set_data_dir(get_data_dir().split(pathsep)[0])
# End use_grids function


class UseGrids:
    """
    Use Grids
    """
    def __init__(self, flag: bool) -> None:
        """
        Initialize the UseGrids class
        """
        super().__init__()
        self._flag: bool = flag
    # End init built-in

    def __enter__(self) -> 'UseGrids':
        """
        Enter
        """
        use_grids(self._flag)
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit
        """
        use_grids(False)
        return False
    # End exit built-in
# End UseGrids class


if __name__ == '__main__':  # pragma: no cover
    pass
