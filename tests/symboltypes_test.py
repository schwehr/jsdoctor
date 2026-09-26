"""Tests for the jsdoctor.symboltypes module."""

import pytest

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


def test_comment_has_flag() -> None:
    """Tests private _comment_has_flag helper in symboltypes."""
    comment = source.Comment("/** @param {string} foo */", 0, 24)

    # Matching flag exists
    # pylint: disable-next=protected-access
    assert symboltypes._comment_has_flag(comment, "@param")

    # Flag does not exist on comment
    # pylint: disable-next=protected-access
    assert not symboltypes._comment_has_flag(comment, "@return")

    # Comment with no flags
    empty_comment = source.Comment("/** Description without flags. */", 0, 32)
    # pylint: disable-next=protected-access
    assert not symboltypes._comment_has_flag(empty_comment, "@param")

    # Flag name without leading '@' raises AssertionError
    with pytest.raises(AssertionError, match="flag name should start with @"):
        # pylint: disable-next=protected-access
        symboltypes._comment_has_flag(comment, "param")
