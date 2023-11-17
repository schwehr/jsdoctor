import unittest

from jsdoctor import namespace


class NamespaceTestCase(unittest.TestCase):

  def testPrototypeProperty(self):
    self.assertTrue(namespace.IsPrototypeProperty('foo.prototype.yes'))
    self.assertFalse(namespace.IsPrototypeProperty('foo.prototype.yes.no'))
    self.assertFalse(namespace.IsPrototypeProperty('foo.prototype.yes.no'))
    self.assertFalse(namespace.IsPrototypeProperty('foo.bar.baz'))

  def testNearestNamespace(self):
    closest = namespace.GetClosestNamespaceForSymbol(
      'aaa.bbb.ccc',
      set(['aaa.bbb.ccc.ddd', 'aaa.bbb.ccc.eee']))
    self.assertIsNone(closest)

    closest = namespace.GetClosestNamespaceForSymbol(
      'aaa.bbb.ccc',
      set(['aaa.bbb', 'aaa.bbb.ccc.ddd']))
    self.assertEqual('aaa.bbb', closest)

    closest = namespace.GetClosestNamespaceForSymbol(
      'goog.string.startsWith',
      set(['goog.string', 'goog.string.Unicode']))
    self.assertEqual('goog.string', closest)

  def testGetNamespaceParts(self):
    self.assertEqual(
      ['goog', 'string', 'startsWith'],
      namespace.GetNamespaceParts('goog.string.startsWith'))

  def testIsSymbolPartOfNamespace(self):
    self.assertTrue(
      namespace.IsSymbolPartOfNamespace(
        'goog.string.startsWith',
        'goog.string'))

    self.assertFalse(
      namespace.IsSymbolPartOfNamespace(
        'goog.string',
        'goog.string.startsWith'))

    self.assertTrue(
      namespace.IsSymbolPartOfNamespace(
        'aaa.bbb.foo',
        'aaa.bbb.foo'))

  def testGetPrototypeProperty(self):
    self.assertEqual(
      'foo', namespace.GetPrototypeProperty('bar.prototype.foo'))
    self.assertRaises(
        AssertionError, lambda: namespace.GetPrototypeProperty('bar'))


if __name__ == '__main__':
    unittest.main()
