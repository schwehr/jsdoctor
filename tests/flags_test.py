import unittest

from jsdoctor import flags
from jsdoctor import source

class FlagTestCase(unittest.TestCase):

  def testParseParamDescription(self):

    desc = '{!bbb|ccc?} aaa This \nis the desc.  '
    self.assertEqual(
      ('aaa', '!bbb|ccc?', 'This \nis the desc.'),
      flags.ParseParameterDescription(desc))

    desc = '{...*} var_args The items to substitute into the pattern.'
    self.assertEqual(
      ('var_args', '...*', 'The items to substitute into the pattern.'),
      flags.ParseParameterDescription(desc))

    desc = '{string} aaa'
    self.assertEqual(
      ('aaa', 'string', ''),
      flags.ParseParameterDescription(desc))

    self.assertRaises(
        ValueError, lambda: flags.ParseParameterDescription('desc without type')
    )

  def testParseReturnDescription(self):

    desc = '  {!bbb|ccc?} This \nis the desc.   '
    self.assertEqual(
      ('!bbb|ccc?', 'This \nis the desc.'),
      flags.ParseReturnDescription(desc))

    self.assertRaises(
        ValueError, lambda: flags.ParseReturnDescription('desc without type')
    )

  def testMabyeParseTypeFromDescription(self):
    self.assertEqual(
      'aaa',
      flags.MaybeParseTypeFromDescription('  {aaa} bbb ccc'))

    self.assertEqual(
      None,
      flags.MaybeParseTypeFromDescription('aaa bbb ccc'))

  @staticmethod
  def GetFlags(script):
    desc, flags = source._GetDescriptionAndFlags(script)
    return flags

  def testGetSymbolType(self):
    self.assertEqual(
      'aaa', flags.GetSymbolType(self.GetFlags("""@const {aaa}""")))
    self.assertEqual(
      'bbb', flags.GetSymbolType(self.GetFlags("""@private {bbb}""")))
    self.assertEqual(
      'ccc', flags.GetSymbolType(self.GetFlags("""@protected {ccc}""")))
    self.assertEqual(
      'ddd', flags.GetSymbolType(self.GetFlags("""@const {ddd}""")))

  def testGetVisibility(self):
    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 * @private
 */
abc.def;
""")
    symbol = list(test_source.symbols)[0]
    comment = symbol.comment
    assert comment is not None  # For pytype.
    self.assertEqual(flags.PRIVATE, flags.GetVisibility(comment.flags))

    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 * @protected
 */
abc.def;
""")
    symbol = list(test_source.symbols)[0]
    self.assertEqual(flags.PROTECTED, flags.GetVisibility(symbol.comment.flags))

    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 */
abc.def;
""")
    symbol = list(test_source.symbols)[0]
    self.assertEqual(flags.PUBLIC, flags.GetVisibility(symbol.comment.flags))


if __name__ == '__main__':
    unittest.main()
