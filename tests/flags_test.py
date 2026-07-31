"""Tests for the jsdoctor.flags module."""

import pytest

from jsdoctor import flags, source


def test_parse_param_description() -> None:
    """Tests parsing of @param JSDoc descriptions."""
    desc = "{!bbb|ccc?} aaa This \nis the desc.  "
    assert flags.ParseParameterDescription(desc) == (
        "aaa",
        "!bbb|ccc?",
        "This \nis the desc.",
    )

    desc = "{...*} var_args The items to substitute into the pattern."
    assert flags.ParseParameterDescription(desc) == (
        "var_args",
        "...*",
        "The items to substitute into the pattern.",
    )

    desc = "{string} aaa"
    assert flags.ParseParameterDescription(desc) == ("aaa", "string", "")

    with pytest.raises(ValueError):
        flags.ParseParameterDescription("desc without type")


def test_parse_return_description() -> None:
    """Tests parsing of @return JSDoc descriptions."""
    desc = "  {!bbb|ccc?} This \nis the desc.   "
    assert flags.ParseReturnDescription(desc) == (
        "!bbb|ccc?",
        "This \nis the desc.",
    )

    with pytest.raises(ValueError):
        flags.ParseReturnDescription("desc without type")


def test_maybe_parse_type_from_description() -> None:
    """Tests parsing type expressions enclosed in braces."""
    assert flags.MaybeParseTypeFromDescription("  {aaa} bbb ccc") == "aaa"
    assert flags.MaybeParseTypeFromDescription("aaa bbb ccc") is None


def _get_flags(script: str):
    """Parses comment flags from a JSDoc script snippet."""
    # pylint: disable-next=protected-access
    _, parsed_flags = source._get_description_and_flags(script)
    return parsed_flags


def test_get_symbol_type() -> None:
    """Tests extracting symbol types from comment flags."""
    assert flags.GetSymbolType(_get_flags("""@const {aaa}""")) == "aaa"
    assert flags.GetSymbolType(_get_flags("""@private {bbb}""")) == "bbb"
    assert flags.GetSymbolType(_get_flags("""@protected {ccc}""")) == "ccc"
    assert flags.GetSymbolType(_get_flags("""@const {ddd}""")) == "ddd"


def test_get_visibility() -> None:
    """Tests determining symbol visibility from comment flags."""
    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 * @private
 */
abc.def;
""")
    symbol = next(iter(test_source.symbols))
    comment = symbol.comment
    assert comment is not None  # For pytype.
    assert flags.GetVisibility(comment.flags) == flags.PRIVATE

    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 * @protected
 */
abc.def;
""")
    symbol = next(iter(test_source.symbols))
    assert symbol.comment is not None
    assert flags.GetVisibility(symbol.comment.flags) == flags.PROTECTED

    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 */
abc.def;
""")
    symbol = next(iter(test_source.symbols))
    assert symbol.comment is not None
    assert flags.GetVisibility(symbol.comment.flags) == flags.PUBLIC
