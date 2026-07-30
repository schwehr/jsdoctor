"""Tests for the jsdoctor.source module."""

import unittest
import unittest.mock

from jsdoctor import scanner
from jsdoctor import source
from jsdoctor import symboltypes


class SourceTestCase(unittest.TestCase):
    """Tests for JavaScript source scanning and symbol extraction."""

    def testScanSource(self):
        """Tests scanning a JavaScript source file into a Source object."""
        test_source = source.ScanScript(_TEST_SCRIPT)
        self.assertEqual({"goog.aaa", "goog.bbb"}, test_source.provides)
        self.assertEqual({"goog.ccc", "goog.ddd"}, test_source.requires)

        self.assertEqual(1, len(test_source.symbols))

        symbol = list(test_source.symbols)[0]
        self.assertEqual("goog.aaa.bbb", symbol.identifier)
        self.assertTrue(symbol.static)
        self.assertEqual("goog.aaa", symbol.namespace)
        self.assertEqual(symboltypes.FUNCTION, symbol.type)

        comment = symbol.comment
        assert comment is not None  # For pytype.
        self.assertEqual("Testing testing.\n@return {string} Dog.", comment.text)

        self.assertEqual(["Testing testing."], comment.description_sections)

        self.assertEqual(1, len(comment.flags))

        flag = comment.flags[0]
        self.assertEqual("@return", flag.name)
        self.assertEqual("{string} Dog.", flag.text)

    def testIsIgnorableIdentifier(self):
        """Tests checking if an identifier match should be ignored."""
        match = scanner.FindCommentTarget("  aaa.bbb = 3")
        self.assertEqual("aaa.bbb", match.group())
        self.assertFalse(source._IsIgnorableIdentifier(match))

        match = scanner.FindCommentTarget("  aaa.bbb(3)")
        self.assertEqual("aaa.bbb", match.group())
        self.assertTrue(source._IsIgnorableIdentifier(match))

        match = scanner.FindCommentTarget("  aaa.bbb[3])")
        self.assertEqual("aaa.bbb", match.group())
        self.assertTrue(source._IsIgnorableIdentifier(match))

    def testScanPrototypeProperty(self):
        """Tests scanning prototype property symbols."""
        test_source = source.ScanScript("""\
goog.provide('abc.Def');

/**
 * Test.
 */
abc.Def.prototype.ghi;
""")
        symbol = list(test_source.symbols)[0]
        self.assertEqual("ghi", symbol.property)
        self.assertFalse(symbol.static)

    def testNamespaceNotFoundError(self):
        """Tests raising NamespaceNotFoundError when no matching namespace is found."""
        match_pairs = scanner.ExtractDocumentedSymbols("/** Test. */\ngoog.aaa.bbb;")
        with unittest.mock.patch.object(
            source.namespace, "GetClosestNamespaceForSymbol", return_value=None
        ):
            with self.assertRaises(source.NamespaceNotFoundError):
                list(source._YieldSymbols(match_pairs, {"goog.aaa"}))

    def testSkipSymbolNotPartOfProvidedNamespace(self):
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
        self.assertEqual(1, len(test_source.symbols))
        symbol = list(test_source.symbols)[0]
        self.assertEqual("goog.aaa.bbb", symbol.identifier)

    def testSkipThisProperties(self):
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
        self.assertEqual(1, len(test_source.symbols))
        symbol = list(test_source.symbols)[0]
        self.assertEqual("goog.aaa.bbb", symbol.identifier)

    def testSkipParenthetical(self):
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
        self.assertEqual(1, len(test_source.symbols))
        symbol = list(test_source.symbols)[0]
        self.assertEqual("goog.aaa.bbb", symbol.identifier)

    def testSkipIgnorableIdentifier(self):
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
        self.assertEqual(1, len(test_source.symbols))
        symbol = list(test_source.symbols)[0]
        self.assertEqual("goog.aaa.bbb", symbol.identifier)

    def testSymbolStr(self):
        """Tests string representation of Symbol objects."""
        sym = source.Symbol("foo.bar", 0, 10)
        self.assertIn("foo.bar", str(sym))
        src = source.Source("var x = 1;", path="path/to/file.js")
        sym.source = src
        self.assertIn("foo.bar", str(sym))
        self.assertIn("path/to/file.js", str(sym))

    def testSourceStr(self):
        """Tests string representation of Source objects."""
        src = source.Source("var x = 1;", path="path/to/file.js")
        self.assertIn("path/to/file.js", str(src))


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
