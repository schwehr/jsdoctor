import unittest

from jsdoctor import scanner
from jsdoctor import source
from jsdoctor import symboltypes


class SourceTestCase(unittest.TestCase):

  def testScanSource(self):

    test_source = source.ScanScript(_TEST_SCRIPT)
    self.assertEqual(
      {'goog.aaa', 'goog.bbb'}, test_source.provides)
    self.assertEqual(
      {'goog.ccc', 'goog.ddd'}, test_source.requires)

    self.assertEqual(1, len(test_source.symbols))

    symbol = list(test_source.symbols)[0]
    self.assertEqual('goog.aaa.bbb', symbol.identifier)
    self.assertTrue(symbol.static)
    self.assertEqual('goog.aaa', symbol.namespace)
    self.assertEqual(symboltypes.FUNCTION, symbol.type)

    comment = symbol.comment
    self.assertEqual('Testing testing.\n@return {string} Dog.', comment.text)

    self.assertEqual(['Testing testing.'], comment.description_sections)

    self.assertEqual(1, len(comment.flags))

    flag = comment.flags[0]
    self.assertEqual('@return', flag.name)
    self.assertEqual('{string} Dog.', flag.text)

  def testIsIgnorableIdentifier(self):
    match = scanner.FindCommentTarget('  aaa.bbb = 3');
    self.assertEqual('aaa.bbb', match.group())
    self.assertFalse(source._IsIgnorableIdentifier(match))

    match = scanner.FindCommentTarget('  aaa.bbb(3)');
    self.assertEqual('aaa.bbb', match.group())
    self.assertTrue(source._IsIgnorableIdentifier(match))

    match = scanner.FindCommentTarget('  aaa.bbb[3])');
    self.assertEqual('aaa.bbb', match.group())
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
    self.assertEqual('ghi', symbol.property)
    self.assertFalse(symbol.static)

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

if __name__ == '__main__':
    unittest.main()
