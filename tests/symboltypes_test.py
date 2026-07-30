"""Tests for the jsdoctor.symboltypes module."""

import unittest

from jsdoctor import scanner, source, symboltypes


def _GetSymbols(script):
    match_pairs = scanner.ExtractDocumentedSymbols(script)
    return list(source._YieldSymbols(match_pairs, {"goog"}))


class SymbolTypesTestCase(unittest.TestCase):
    """Tests for determining JavaScript symbol types."""

    def assertSymbolType(self, expected_type, script):
        """Asserts that a script snippet yields a symbol of expected type."""
        symbol = _GetSymbols(script)[0]
        self.assertEqual(expected_type, symboltypes.DetermineSymbolType(symbol))

    def testDetermineSymbolType(self):
        """Tests determining symbol types from JSDoc tags and identifiers."""
        self.assertSymbolType(
            symboltypes.PROPERTY,
            """
/**
 * Cat's cradle.
 */
goog.bar.baz
""",
        )

        self.assertSymbolType(
            symboltypes.FUNCTION,
            """
/**
 * @param foo
 */
goog.bar.baz
""",
        )

        self.assertSymbolType(
            symboltypes.FUNCTION,
            """
/**
 * @return foo
 */
goog.bar.baz
""",
        )

        self.assertSymbolType(
            symboltypes.ENUM,
            """
/**
 * @enum {string}
 */
goog.bar.baz
""",
        )

        self.assertSymbolType(
            symboltypes.CONSTRUCTOR,
            """
/**
 * @constructor
 */
goog.bar.baz
""",
        )

        self.assertSymbolType(
            symboltypes.INTERFACE,
            """
/**
 * @interface
 */
goog.bar.baz
""",
        )
