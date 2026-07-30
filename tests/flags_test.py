"""Tests for the jsdoctor.flags module."""

import unittest

from jsdoctor import flags, source


class FlagTestCase(unittest.TestCase):
    """Tests for parsing and handling JSDoc flags."""

    def test_parse_param_description(self):
        """Tests parsing of @param JSDoc descriptions."""
        desc = "{!bbb|ccc?} aaa This \nis the desc.  "
        self.assertEqual(
            ("aaa", "!bbb|ccc?", "This \nis the desc."),
            flags.ParseParameterDescription(desc),
        )

        desc = "{...*} var_args The items to substitute into the pattern."
        self.assertEqual(
            ("var_args", "...*", "The items to substitute into the pattern."),
            flags.ParseParameterDescription(desc),
        )

        desc = "{string} aaa"
        self.assertEqual(("aaa", "string", ""), flags.ParseParameterDescription(desc))

        self.assertRaises(
            ValueError, lambda: flags.ParseParameterDescription("desc without type")
        )

    def test_parse_return_description(self):
        """Tests parsing of @return JSDoc descriptions."""
        desc = "  {!bbb|ccc?} This \nis the desc.   "
        self.assertEqual(
            ("!bbb|ccc?", "This \nis the desc."), flags.ParseReturnDescription(desc)
        )

        self.assertRaises(
            ValueError, lambda: flags.ParseReturnDescription("desc without type")
        )

    def test_maybe_parse_type_from_description(self):
        """Tests parsing type expressions enclosed in braces."""
        self.assertEqual("aaa", flags.MaybeParseTypeFromDescription("  {aaa} bbb ccc"))

        self.assertEqual(None, flags.MaybeParseTypeFromDescription("aaa bbb ccc"))

    @staticmethod
    def get_flags(script):
        """Parses comment flags from a JSDoc script snippet."""
        # pylint: disable-next=protected-access
        _, parsed_flags = source._get_description_and_flags(script)
        return parsed_flags

    def test_get_symbol_type(self):
        """Tests extracting symbol types from comment flags."""
        self.assertEqual("aaa", flags.GetSymbolType(self.get_flags("""@const {aaa}""")))
        self.assertEqual(
            "bbb", flags.GetSymbolType(self.get_flags("""@private {bbb}"""))
        )
        self.assertEqual(
            "ccc", flags.GetSymbolType(self.get_flags("""@protected {ccc}"""))
        )
        self.assertEqual("ddd", flags.GetSymbolType(self.get_flags("""@const {ddd}""")))

    def test_get_visibility(self):
        """Tests determining symbol visibility from comment flags."""
        test_source = source.ScanScript("""\
goog.provide('abc');

/**
 * @private
 */
abc.def;
""")
        symbol = list(test_source.symbols)[0]
        comment = symbol.comment
        assert comment is not None  # For pytype.
        self.assertEqual(flags.PRIVATE, flags.GetVisibility(comment.flags))

        test_source = source.ScanScript("""\
goog.provide('abc');

/**
 * @protected
 */
abc.def;
""")
        symbol = list(test_source.symbols)[0]
        self.assertEqual(flags.PROTECTED, flags.GetVisibility(symbol.comment.flags))

        test_source = source.ScanScript("""\
goog.provide('abc');

/**
 */
abc.def;
""")
        symbol = list(test_source.symbols)[0]
        self.assertEqual(flags.PUBLIC, flags.GetVisibility(symbol.comment.flags))
