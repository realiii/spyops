# -*- coding: utf-8 -*-
"""
Validation tests for Files
"""


from pathlib import Path

from pytest import mark, raises

from spyops.validation import ValidateFile

pytestmark = [mark.validation]


class TestValidateFile:
    """
    Test Validate File
    """
    @mark.parametrize('ext, expected', [
        (None, None),
        (' ', None),
        ('txt', '.txt'),
        ('.txt', '.txt'),
    ])
    def test_check_extension(self, ext, expected):
        """
        Test check extension
        """
        assert ValidateFile._check_extension(ext) == expected
    # End test_check_extension method

    @mark.parametrize('path, expected', [
        (None, None),
        (' ', None),
        ('a/b/c.def', Path('a/b/c.def')),
    ])
    def test_get_object(self, path, expected):
        """
        Test get object
        """
        name = 'path'
        vf = ValidateFile(name)
        assert vf._get_object({name: path}) == expected
    # End test_get_object method

    @mark.parametrize('path, ext, expected', [
        (Path('/a/b/c.def'), None, Path('/a/b/c.def')),
        (Path('/a/b/c.def'), 'txt', Path('/a/b/c.txt')),
        (Path('/a/b/c.def'), '.txt', Path('/a/b/c.txt')),
    ])
    def test_make_path(self, path, ext, expected):
        """
        Test make path
        """
        vf = ValidateFile('path', extension=ext)
        assert vf._make_path(path) == expected
    # End test_make_path method

    def test_check_path(self, nrn_geopackage):
        """
        Test check path
        """
        vf = ValidateFile('path', is_output=False)
        with raises(FileNotFoundError):
            vf._check_path(Path('/a/b/c.def'))
        vf = ValidateFile('path')
        with raises(FileExistsError):
            vf._check_path(nrn_geopackage.path)
    # End test_check_path method
# End TestValidateFile class


if __name__ == '__main__':  # pragma: no cover
    pass
