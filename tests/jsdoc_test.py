"""Tests for the jsdoctor.jsdoc module."""

import unittest

from jsdoctor import jsdoc


class JsDocTestCase(unittest.TestCase):
    """Tests for JSDoc comment processing and section extraction."""

    def test_process_comment(self):
        """Tests comment sectioning and flag parsing."""
        descriptions, flags = jsdoc.ProcessComment(_SCRIPT)

        self.assertEqual(
            [
                ("@flag", "Thing thing"),
                ("@flag2", "More thing."),
                ("@flag3", "More thing and\nmore thing."),
                ("@flag4", "One last thing."),
            ],
            flags,
        )

        self.assertEqual(["This is a comment.", "End of thing."], descriptions)

    def test_split_sections(self):
        """Tests splitting comment blocks into section strings."""
        parts = list(jsdoc._yield_sections(_SCRIPT))
        self.assertEqual(
            [
                "@flag Thing thing",
                "This is a comment.",
                "@flag2 More thing.\n@flag3 More thing and\nmore thing.",
                "End of thing.\n@flag4 One last thing.",
            ],
            parts,
        )

    def test_match_flags(self):
        """Tests matching flag regex against comment text."""
        matches = jsdoc._match_flags(_SCRIPT)
        flags = [match.group("flag") for match in matches]
        self.assertEqual(["@flag", "@flag2", "@flag3", "@flag4"], flags)


_SCRIPT = """\
@flag Thing thing


This is a comment.

@flag2 More thing.
@flag3 More thing and
more thing.

End of thing.
@flag4 One last thing.
"""
