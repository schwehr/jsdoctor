"""Tests for the jsdoctor.symboltypes module."""

from jsdoctor import scanner, source, symboltypes


def _get_symbols(script: str) -> list[source.Symbol]:
    match_pairs = scanner.ExtractDocumentedSymbols(script)
    # pylint: disable-next=protected-access
    return list(source._yield_symbols(match_pairs, {"goog"}))


def _assert_symbol_type(expected_type: str, script: str) -> None:
    """Asserts that a script snippet yields a symbol of expected type."""
    symbol = _get_symbols(script)[0]
    assert symboltypes.DetermineSymbolType(symbol) == expected_type


def test_determine_symbol_type() -> None:
    """Tests determining symbol types from JSDoc tags and identifiers."""
    _assert_symbol_type(
        symboltypes.PROPERTY,
        """
/**
 * Cat's cradle.
 */
goog.bar.baz
""",
    )

    _assert_symbol_type(
        symboltypes.FUNCTION,
        """
/**
 * @param foo
 */
goog.bar.baz
""",
    )

    _assert_symbol_type(
        symboltypes.FUNCTION,
        """
/**
 * @return foo
 */
goog.bar.baz
""",
    )

    _assert_symbol_type(
        symboltypes.ENUM,
        """
/**
 * @enum {string}
 */
goog.bar.baz
""",
    )

    _assert_symbol_type(
        symboltypes.CONSTRUCTOR,
        """
/**
 * @constructor
 */
goog.bar.baz
""",
    )

    _assert_symbol_type(
        symboltypes.INTERFACE,
        """
/**
 * @interface
 */
goog.bar.baz
""",
    )
