"""Tests for the jsdoctor.source module."""

from unittest import mock

import pytest

from jsdoctor import scanner, source, symboltypes


def test_scan_source() -> None:
    """Tests scanning a JavaScript source file into a Source object."""
    test_source = source.ScanScript(_TEST_SCRIPT)
    assert test_source.provides == {"goog.aaa", "goog.bbb"}
    assert test_source.requires == {"goog.ccc", "goog.ddd"}

    assert len(test_source.symbols) == 1

    symbol = next(iter(test_source.symbols))
    assert symbol.identifier == "goog.aaa.bbb"
    assert symbol.static
    assert symbol.namespace == "goog.aaa"
    assert symbol.type == symboltypes.FUNCTION

    comment = symbol.comment
    assert comment is not None  # For pytype.
    assert comment.text == "Testing testing.\n@return {string} Dog."

    assert comment.description_sections == ["Testing testing."]

    assert len(comment.flags) == 1

    flag = comment.flags[0]
    assert flag.name == "@return"
    assert flag.text == "{string} Dog."


def test_is_ignorable_identifier() -> None:
    """Tests checking if an identifier match should be ignored."""
    match = scanner.FindCommentTarget("  aaa.bbb = 3")
    assert match is not None
    assert match.group() == "aaa.bbb"
    # pylint: disable-next=protected-access
    assert not source._is_ignorable_identifier(match)

    match = scanner.FindCommentTarget("  aaa.bbb(3)")
    assert match is not None
    assert match.group() == "aaa.bbb"
    # pylint: disable-next=protected-access
    assert source._is_ignorable_identifier(match)

    match = scanner.FindCommentTarget("  aaa.bbb[3])")
    assert match is not None
    assert match.group() == "aaa.bbb"
    # pylint: disable-next=protected-access
    assert source._is_ignorable_identifier(match)


def test_scan_prototype_property() -> None:
    """Tests scanning prototype property symbols."""
    test_source = source.ScanScript("""\
goog.provide('abc.Def');

/**
 * Test.
 */
abc.Def.prototype.ghi;
""")
    symbol = next(iter(test_source.symbols))
    assert symbol.property == "ghi"
    assert not symbol.static


def test_namespace_not_found_error() -> None:
    """Tests raising NamespaceNotFoundError when no matching namespace is found."""
    match_pairs = scanner.ExtractDocumentedSymbols("/** Test. */\ngoog.aaa.bbb;")
    with (
        mock.patch.object(
            source.namespace,
            "GetClosestNamespaceForSymbol",
            return_value=None,
        ),
        pytest.raises(source.NamespaceNotFoundError),
    ):
        # pylint: disable-next=protected-access
        list(source._yield_symbols(match_pairs, {"goog.aaa"}))


def test_skip_symbol_not_part_of_provided_namespace() -> None:
    """Tests skipping symbols outside provided namespaces."""
    test_source = source.ScanScript("""\
goog.provide('goog.aaa');

/**
 * Symbol not in provided namespace.
 */
other.namespace.Symbol;

/**
 * Symbol in provided namespace.
 */
goog.aaa.bbb;
""")
    assert len(test_source.symbols) == 1
    symbol = next(iter(test_source.symbols))
    assert symbol.identifier == "goog.aaa.bbb"


def test_skip_this_properties() -> None:
    """Tests skipping properties set on this."""
    test_source = source.ScanScript("""\
goog.provide('goog.aaa');

/**
 * Property on this.
 */
this.foo = 1;

/**
 * Symbol in provided namespace.
 */
goog.aaa.bbb;
""")
    assert len(test_source.symbols) == 1
    symbol = next(iter(test_source.symbols))
    assert symbol.identifier == "goog.aaa.bbb"


def test_skip_parenthetical() -> None:
    """Tests skipping parenthetical expressions following JSDoc comments."""
    test_source = source.ScanScript("""\
goog.provide('goog.aaa');

/**
 * Type cast on parenthetical.
 */
(x + y);

/**
 * Symbol in provided namespace.
 */
goog.aaa.bbb;
""")
    assert len(test_source.symbols) == 1
    symbol = next(iter(test_source.symbols))
    assert symbol.identifier == "goog.aaa.bbb"


def test_skip_ignorable_identifier() -> None:
    """Tests skipping ignorable identifier calls following JSDoc comments."""
    test_source = source.ScanScript("""\
goog.provide('goog.aaa');

/**
 * Type cast on method call.
 */
goog.aaa.ccc(3);

/**
 * Symbol in provided namespace.
 */
goog.aaa.bbb;
""")
    assert len(test_source.symbols) == 1
    symbol = next(iter(test_source.symbols))
    assert symbol.identifier == "goog.aaa.bbb"


def test_symbol_str() -> None:
    """Tests string representation of Symbol objects."""
    sym = source.Symbol("foo.bar", 0, 10)
    assert "foo.bar" in str(sym)
    src = source.Source("var x = 1;", path="path/to/file.js")
    sym.source = src
    assert "foo.bar" in str(sym)
    assert "path/to/file.js" in str(sym)


def test_source_str() -> None:
    """Tests string representation of Source objects."""
    src = source.Source("var x = 1;", path="path/to/file.js")
    assert "path/to/file.js" in str(src)


def test_get_description_and_flags() -> None:
    """Tests parsing comment text into descriptions and Flag objects."""
    comment_text = (
        "Description line 1.\n"
        "Description line 2.\n"
        "@param {string} name User name.\n"
        "@return {boolean} Success status."
    )
    # pylint: disable-next=protected-access
    descriptions, flags = source._get_description_and_flags(comment_text)

    assert descriptions == ["Description line 1.\nDescription line 2."]
    assert len(flags) == 2

    assert flags[0].name == "@param"
    assert flags[0].text == "{string} name User name."

    assert flags[1].name == "@return"
    assert flags[1].text == "{boolean} Success status."


def test_get_description_and_flags_description_only() -> None:
    """Tests description-only text in _get_description_and_flags."""
    # pylint: disable-next=protected-access
    descriptions, flags = source._get_description_and_flags("Just a description.")
    assert descriptions == ["Just a description."]
    assert not flags


def test_get_description_and_flags_flags_only() -> None:
    """Tests flags-only text in _get_description_and_flags."""
    # pylint: disable-next=protected-access
    descriptions, flags = source._get_description_and_flags("@private\n@const")
    assert not descriptions
    assert len(flags) == 2
    assert flags[0].name == "@private"
    assert flags[0].text == ""
    assert flags[1].name == "@const"
    assert flags[1].text == ""


def test_get_description_and_flags_empty() -> None:
    """Tests empty comment text in _get_description_and_flags."""
    # pylint: disable-next=protected-access
    descriptions, flags = source._get_description_and_flags("")
    assert not descriptions
    assert not flags


_TEST_SCRIPT = """
goog.provide('goog.aaa');
goog.provide('goog.bbb');

goog.require('goog.ccc');
goog.require('goog.ddd');

/**
 * Testing testing.
 * @return {string} Dog.
 */
goog.aaa.bbb;
"""
