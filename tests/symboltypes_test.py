"""Tests for the jsdoctor.symboltypes module."""

import unittest

from jsdoctor import scanner, source, symboltypes


def _get_symbols(script):
    match_pairs = scanner.ExtractDocumentedSymbols(script)
    # pylint: disable-next=protected-access
    return list(source._yield_symbols(match_pairs, {"goog"}))


class SymbolTypesTestCase(unittest.TestCase):
    """Tests for determining JavaScript symbol types."""

    def assert_symbol_type(self, expected_type, script):
        """Asserts that a script snippet yields a symbol of expected type."""
        symbol = _get_symbols(script)[0]
        self.assertEqual(expected_type, symboltypes.DetermineSymbolType(symbol))

    def test_determine_symbol_type(self):
        """Tests determining symbol types from JSDoc tags and identifiers."""
        self.assert_symbol_type(
            symboltypes.PROPERTY,
            """
/**
 * Cat's cradle.
 */
goog.bar.baz
""",
        )

        self.assert_symbol_type(
            symboltypes.FUNCTION,
            """
/**
 * @param foo
 */
goog.bar.baz
""",
        )

        self.assert_symbol_type(
            symboltypes.FUNCTION,
            """
/**
 * @return foo
 */
goog.bar.baz
""",
        )

        self.assert_symbol_type(
            symboltypes.ENUM,
            """
/**
 * @enum {string}
 */
goog.bar.baz
""",
        )

        self.assert_symbol_type(
            symboltypes.CONSTRUCTOR,
            """
/**
 * @constructor
 */
goog.bar.baz
""",
        )

        self.assert_symbol_type(
            symboltypes.INTERFACE,
            """
/**
 * @interface
 */
goog.bar.baz
""",
        )
