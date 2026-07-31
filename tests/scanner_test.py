"""Tests for the jsdoctor.scanner module."""

import pytest

from jsdoctor import scanner


def test_provides() -> None:
    """Tests extracting goog.provide and goog.require statements."""
    source_text = """
goog.provide('goog.dom');
goog.provide('goog.style');

goog.require('goog.array');
goog.require('goog.string');
"""
    provides = list(scanner.YieldProvides(source_text))
    requires = list(scanner.YieldRequires(source_text))

    assert provides == ["goog.dom", "goog.style"]
    assert requires == ["goog.array", "goog.string"]


def test_find_doc_comments() -> None:
    """Tests searching for JSDoc comment blocks."""
    matches = list(scanner.FindJsDocComments(_TEST_SCRIPT))
    assert len(matches) == 1

    match = matches[0]
    assert match.start() == 10
    assert match.end() == 34


def test_find_identifier() -> None:
    """Tests finding the identifier target following a JSDoc comment."""
    match = next(iter(scanner.FindJsDocComments(_TEST_SCRIPT)))
    identifier_match = scanner.FindCommentTarget(match.string, match.end())
    assert identifier_match is not None
    assert identifier_match.group() == "goog.bar.baz"


def test_find_weird_identifier() -> None:
    """Tests finding identifiers containing special characters like $."""
    script = "     \n   \n $aa$.b$b.cc$   "
    identifier_match = scanner.FindCommentTarget(script)
    assert identifier_match is not None
    assert identifier_match.group() == "$aa$.b$b.cc$"


def test_extract_text() -> None:
    """Tests extracting clean text from a JSDoc comment block."""
    script = """
/**
 * Slaughterhouse five.
 *
 * @return {string} The result, as a string.
 */
"""

    match = next(iter(scanner.FindJsDocComments(script)))
    comment = match.group()
    text = scanner.ExtractTextFromJsDocComment(comment)
    assert text == "Slaughterhouse five.\n\n@return {string} The result, as a string."


def test_extract_documented_symbols() -> None:
    """Tests extracting comment-identifier pairs from source."""
    script = """
/**
 * Test goog dom.
 *
 * One two three.
 */
goog.dom.test

/**
 * Test goog style.
 *
 * Four five six.
 */
goog.style.test
"""

    pairs = list(scanner.ExtractDocumentedSymbols(script))

    assert len(pairs) == 2

    comment_match, symbol_match = pairs[0]
    assert comment_match.group() == "/**\n * Test goog dom.\n *\n * One two three.\n */"
    assert symbol_match is not None
    assert symbol_match.group() == "goog.dom.test"

    comment_match, symbol_match = pairs[1]
    assert (
        comment_match.group() == "/**\n * Test goog style.\n *\n * Four five six.\n */"
    )
    assert symbol_match is not None
    assert symbol_match.group() == "goog.style.test"


def test_strip_whitespace() -> None:
    """Tests stripping all whitespace characters from strings."""
    assert scanner.StripWhitespace("nospaces") == "nospaces"
    assert scanner.StripWhitespace("  leading") == "leading"
    assert scanner.StripWhitespace("trailing  ") == "trailing"
    assert scanner.StripWhitespace("  both  ") == "both"
    assert scanner.StripWhitespace("\t\ttabs\t\t") == "tabs"
    assert scanner.StripWhitespace("   \t  ") == ""


def test_odd_identifier() -> None:
    """Tests extracting multiline or formatted identifiers."""
    test_script = """\
/**
 * Moose.
 */
goog
.
bar.
baz   .
qux =
"""

    match = next(iter(scanner.FindJsDocComments(test_script)))
    identifier_match = scanner.FindCommentTarget(match.string, match.end())
    assert identifier_match is not None
    symbol = scanner.StripWhitespace(identifier_match.group())
    assert symbol == "goog.bar.baz.qux"


def test_cast() -> None:
    """Tests finding opening parenthesis targets for type casts."""
    identifier_match = scanner.FindCommentTarget("   (aaa)")
    assert identifier_match is not None
    assert identifier_match.group() == "("


def test_file_overview_comment() -> None:
    """Tests handling @fileoverview comments without identifier targets."""
    script = "/**\n * @fileoverview Description of file.\n */"
    pairs = list(scanner.ExtractDocumentedSymbols(script))
    assert len(pairs) == 1
    _, identifier_match = pairs[0]
    assert identifier_match is None


def test_no_identifier_found_error() -> None:
    """Tests raising NoIdentifierFoundError when no target follows a comment."""
    script = "/**\n * Comment with no target.\n */\n"
    with pytest.raises(scanner.NoIdentifierFoundError):
        list(scanner.ExtractDocumentedSymbols(script))


_TEST_SCRIPT = """\
var = 2;

/**
 * Cat's cradle.
 */
goog.bar.baz
"""
