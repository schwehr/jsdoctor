"""Tests for the jsdoctor.cli module."""

import unittest

from jsdoctor import cli


class CliTest(unittest.TestCase):
    """Tests for cli functions."""

    def test_should_scan_path(self) -> None:
        # pylint: disable=protected-access
        """Tests the _should_scan_path path filtering logic."""
        # Happy paths
        self.assertTrue(cli._should_scan_path("foo.js"))
        self.assertTrue(cli._should_scan_path("some/dir/foo.js"))
        self.assertTrue(cli._should_scan_path("/absolute/path/bar.js"))

        # Not ending in .js
        self.assertFalse(cli._should_scan_path("foo.txt"))
        self.assertFalse(cli._should_scan_path("foo.js.txt"))
        self.assertFalse(cli._should_scan_path("foo.json"))
        self.assertFalse(cli._should_scan_path("no_extension"))

        # deps.js
        self.assertFalse(cli._should_scan_path("deps.js"))
        self.assertFalse(cli._should_scan_path("some/dir/deps.js"))

        # _test.js
        self.assertFalse(cli._should_scan_path("foo_test.js"))
        self.assertFalse(cli._should_scan_path("some/dir/foo_test.js"))

        # Some weirdly named files but technically valid
        self.assertTrue(cli._should_scan_path("deps_foo.js"))
        self.assertTrue(cli._should_scan_path("test.js"))
        self.assertTrue(cli._should_scan_path("foo-test.js"))
        self.assertTrue(cli._should_scan_path(".js"))


if __name__ == "__main__":
    unittest.main()
