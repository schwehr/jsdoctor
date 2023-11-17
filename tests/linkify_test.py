import unittest

from jsdoctor import linkify


class LinkifyTestCase(unittest.TestCase):

  def testWebRegEx(self):
    match = linkify._WEB_URL_RE.search('aaa http://google.com bbb')
    self.assertIsNotNone(match)
    self.assertEqual('http://google.com', match.group(0))

  def testLinkifyWebUrls(self):
    self.assertEqual(
      'aaa <a href="http://google.com">http://google.com</a> bbb',
      linkify.LinkifyWebUrls('aaa http://google.com bbb'))

  def testMatchSymbols(self):
    matches = linkify._SYMBOL_RE.finditer('aaa goog.dom#cars bb.cc')
    match_strings = [match.group(0) for match in matches]

    self.assertEqual(
        ['aaa', 'goog.dom#cars', 'bb.cc'],
        match_strings)

  def testLinkifySymbols(self):
    self.assertEqual(
        'aaa <a href="goog.dom.html">goog.dom#cars</a> bb.cc',
        linkify.LinkifySymbols('aaa goog.dom#cars bb.cc', set(['goog.dom'])))

if __name__ == '__main__':
    unittest.main()
