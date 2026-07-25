import unittest
import unittest.mock

from jsdoctor import scanner
from jsdoctor import source
from jsdoctor import symboltypes


class SourceTestCase(unittest.TestCase):
    def testScanSource(self):
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
        match_pairs = scanner.ExtractDocumentedSymbols("/** Test. */\ngoog.aaa.bbb;")
        with unittest.mock.patch.object(
            source.namespace, "GetClosestNamespaceForSymbol", return_value=None
        ):
            with self.assertRaises(source.NamespaceNotFoundError):
                list(source._YieldSymbols(match_pairs, {"goog.aaa"}))

    def testSkipSymbolNotPartOfProvidedNamespace(self):
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
        sym = source.Symbol("foo.bar", 0, 10)
        self.assertIn("foo.bar", str(sym))
        src = source.Source("var x = 1;", path="path/to/file.js")
        sym.source = src
        self.assertIn("foo.bar", str(sym))
        self.assertIn("path/to/file.js", str(sym))

    def testSourceStr(self):
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
