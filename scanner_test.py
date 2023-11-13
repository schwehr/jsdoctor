import scanner
import unittest

class ScannerTestCase(unittest.TestCase):

  def testProvides(self):
    source = """
goog.provide('goog.dom');
goog.provide('goog.style');

goog.require('goog.array');
goog.require('goog.string');
"""
    provides = list(scanner.YieldProvides(source))
    requires = list(scanner.YieldRequires(source))

    self.assertEqual(['goog.dom', 'goog.style'], provides)
    self.assertEqual(['goog.array', 'goog.string'], requires)


  def testFindDocComments(self):
    matches = list(scanner.FindJsDocComments(_TEST_SCRIPT))
    self.assertEqual(1, len(matches))

    match = matches[0]
    self.assertEqual(10, match.start())
    self.assertEqual(34, match.end())

  def testFindIdentifier(self):
    match = list(scanner.FindJsDocComments(_TEST_SCRIPT))[0]
    identifier_match = scanner.FindCommentTarget(match.string, match.end())
    self.assertEqual('goog.bar.baz', identifier_match.group())

  def testFindWeirdIdentifier(self):
    script = '     \n   \n $aa$.b$b.cc$   '
    identifier_match = scanner.FindCommentTarget(script)
    self.assertEqual('$aa$.b$b.cc$', identifier_match.group())

  def testExtractText(self):
    script = """
/**
 * Slaughterhouse five.
 *
 * @return {string} The result, as a string.
 */
"""

    match = list(scanner.FindJsDocComments(script))[0]
    comment = match.group()
    text = scanner.ExtractTextFromJsDocComment(comment)
    self.assertEqual('Slaughterhouse five.\n\n' +
                      '@return {string} The result, as a string.',
                      text)

  def testExtractDocumentedSymbols(self):
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
      '/**\n * Test goog dom.\n *\n * One two three.\n */',
      comment_match.group())
    self.assertEqual('goog.dom.test', symbol_match.group())

    comment_match, symbol_match = pairs[1]
    self.assertEqual(
      '/**\n * Test goog style.\n *\n * Four five six.\n */',
      comment_match.group())
    self.assertEqual('goog.style.test', symbol_match.group())


  def testOddIdentifier(self):
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

    match = list(scanner.FindJsDocComments(test_script))[0]
    identifier_match = scanner.FindCommentTarget(match.string, match.end())
    symbol = scanner.StripWhitespace(identifier_match.group())
    self.assertEqual('goog.bar.baz.qux', symbol)

  def testCast(self):

    identifier_match = scanner.FindCommentTarget('   (aaa)')
    self.assertEqual('(', identifier_match.group())

_TEST_SCRIPT = """\
var = 2;

/**
 * Cat's cradle.
 */
goog.bar.baz
"""



if __name__ == '__main__':
    unittest.main()



