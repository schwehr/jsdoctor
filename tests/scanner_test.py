"""Tests for the jsdoctor.scanner module."""

import unittest

from jsdoctor import scanner


class ScannerTestCase(unittest.TestCase):
    """Tests for regex scanners extracting Closure declarations and comments."""

    def test_provides(self):
        """Tests extracting goog.provide and goog.require statements."""
        source = """
goog.provide('goog.dom');
goog.provide('goog.style');

goog.require('goog.array');
goog.require('goog.string');
"""
        provides = list(scanner.YieldProvides(source))
        requires = list(scanner.YieldRequires(source))

        self.assertEqual(["goog.dom", "goog.style"], provides)
        self.assertEqual(["goog.array", "goog.string"], requires)

    def test_find_doc_comments(self):
        """Tests searching for JSDoc comment blocks."""
        matches = list(scanner.FindJsDocComments(_TEST_SCRIPT))
        self.assertEqual(1, len(matches))

        match = matches[0]
        self.assertEqual(10, match.start())
        self.assertEqual(34, match.end())

    def test_find_identifier(self):
        """Tests finding the identifier target following a JSDoc comment."""
        match = next(iter(scanner.FindJsDocComments(_TEST_SCRIPT)))
        identifier_match = scanner.FindCommentTarget(match.string, match.end())
        self.assertEqual("goog.bar.baz", identifier_match.group())

    def test_find_weird_identifier(self):
        """Tests finding identifiers containing special characters like $."""
        script = "     \n   \n $aa$.b$b.cc$   "
        identifier_match = scanner.FindCommentTarget(script)
        self.assertEqual("$aa$.b$b.cc$", identifier_match.group())

    def test_extract_text(self):
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
        self.assertEqual(
            "Slaughterhouse five.\n\n" + "@return {string} The result, as a string.",
            text,
        )

    def test_extract_documented_symbols(self):
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

        self.assertEqual(2, len(pairs))

        comment_match, symbol_match = pairs[0]
        self.assertEqual(
            "/**\n * Test goog dom.\n *\n * One two three.\n */", comment_match.group()
        )
        self.assertEqual("goog.dom.test", symbol_match.group())

        comment_match, symbol_match = pairs[1]
        self.assertEqual(
            "/**\n * Test goog style.\n *\n * Four five six.\n */",
            comment_match.group(),
        )
        self.assertEqual("goog.style.test", symbol_match.group())

    def test_strip_whitespace(self):
        """Tests stripping all whitespace characters from strings."""
        self.assertEqual("nospaces", scanner.StripWhitespace("nospaces"))
        self.assertEqual("leading", scanner.StripWhitespace("  leading"))
        self.assertEqual("trailing", scanner.StripWhitespace("trailing  "))
        self.assertEqual("both", scanner.StripWhitespace("  both  "))
        self.assertEqual("tabs", scanner.StripWhitespace("\t\ttabs\t\t"))
        self.assertEqual("", scanner.StripWhitespace("   \t  "))

    def test_odd_identifier(self):
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
        symbol = scanner.StripWhitespace(identifier_match.group())
        self.assertEqual("goog.bar.baz.qux", symbol)

    def test_cast(self):
        """Tests finding opening parenthesis targets for type casts."""
        identifier_match = scanner.FindCommentTarget("   (aaa)")
        self.assertEqual("(", identifier_match.group())

    def test_file_overview_comment(self):
        """Tests handling @fileoverview comments without identifier targets."""
        script = "/**\n * @fileoverview Description of file.\n */"
        pairs = list(scanner.ExtractDocumentedSymbols(script))
        self.assertEqual(1, len(pairs))
        _, identifier_match = pairs[0]
        self.assertIsNone(identifier_match)

    def test_no_identifier_found_error(self):
        """Tests raising NoIdentifierFoundError when no target follows a comment."""
        script = "/**\n * Comment with no target.\n */\n"
        with self.assertRaises(scanner.NoIdentifierFoundError):
            list(scanner.ExtractDocumentedSymbols(script))


_TEST_SCRIPT = """\
var = 2;

/**
 * Cat's cradle.
 */
goog.bar.baz
"""
