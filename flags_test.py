
import flags
import unittest
import re
import source

class FlagTestCase(unittest.TestCase):

  def testParseParamDescription(self):

    desc = '{!bbb|ccc?} aaa This \nis the desc.  '
    self.assertEquals(
      ('aaa', '!bbb|ccc?', 'This \nis the desc.'),
      flags.ParseParameterDescription(desc))

    desc = '{...*} var_args The items to substitute into the pattern.'
    self.assertEquals(
      ('var_args', '...*', 'The items to substitute into the pattern.'),
      flags.ParseParameterDescription(desc))


    desc = '{string} aaa'
    self.assertEquals(
      ('aaa', 'string', ''),
      flags.ParseParameterDescription(desc))

    self.assertRaises(
      ValueError,
      lambda: flags.ParseParameterDescription('desc without type'))

  def testParseReturnDescription(self):

    desc = '  {!bbb|ccc?} This \nis the desc.   '
    self.assertEquals(
      ('!bbb|ccc?', 'This \nis the desc.'),
      flags.ParseReturnDescription(desc))

    self.assertRaises(
      ValueError,
      lambda: flags.ParseReturnDescription('desc without type'))

  def testMabyeParseTypeFromDescription(self):
    self.assertEquals(
      'aaa',
      flags.MaybeParseTypeFromDescription('  {aaa} bbb ccc'))

    self.assertEquals(
      None,
      flags.MaybeParseTypeFromDescription('aaa bbb ccc'))

  @staticmethod
  def GetFlags(script):
    desc, flags = source._GetDescriptionAndFlags(script)
    return flags

  def testGetSymbolType(self):
    self.assertEquals(
      'aaa', flags.GetSymbolType(self.GetFlags("""@const {aaa}""")))
    self.assertEquals(
      'bbb', flags.GetSymbolType(self.GetFlags("""@private {bbb}""")))
    self.assertEquals(
      'ccc', flags.GetSymbolType(self.GetFlags("""@protected {ccc}""")))
    self.assertEquals(
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
    self.assertEquals(flags.PRIVATE, flags.GetVisibility(symbol.comment.flags))

    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 * @protected
 */
abc.def;
""")
    symbol = list(test_source.symbols)[0]
    self.assertEquals(flags.PROTECTED, flags.GetVisibility(symbol.comment.flags))

    test_source = source.ScanScript("""\
goog.provide('abc');

/**
 */
abc.def;
""")
    symbol = list(test_source.symbols)[0]
    self.assertEquals(flags.PUBLIC, flags.GetVisibility(symbol.comment.flags))



if __name__ == '__main__':
    unittest.main()



