"""Tests for the jsdoctor.namespace module."""

import unittest

from jsdoctor import namespace


class NamespaceTestCase(unittest.TestCase):
    """Tests for namespace manipulation and checking helpers."""

    def test_prototype_property(self):
        """Tests identifying prototype property namespaces."""
        self.assertTrue(namespace.IsPrototypeProperty("foo.prototype.yes"))
        self.assertFalse(namespace.IsPrototypeProperty("foo.prototype.yes.no"))
        self.assertFalse(namespace.IsPrototypeProperty("foo.prototype.yes.no"))
        self.assertFalse(namespace.IsPrototypeProperty("foo.bar.baz"))

    def test_nearest_namespace(self):
        """Tests finding closest matching namespace for symbols."""
        closest = namespace.GetClosestNamespaceForSymbol(
            "aaa.bbb.ccc", {"aaa.bbb.ccc.ddd", "aaa.bbb.ccc.eee"}
        )
        self.assertIsNone(closest)

        closest = namespace.GetClosestNamespaceForSymbol(
            "aaa.bbb.ccc", {"aaa.bbb", "aaa.bbb.ccc.ddd"}
        )
        self.assertEqual("aaa.bbb", closest)

        closest = namespace.GetClosestNamespaceForSymbol(
            "goog.string.startsWith", {"goog.string", "goog.string.Unicode"}
        )
        self.assertEqual("goog.string", closest)

    def test_get_namespace_parts(self):
        """Tests splitting namespaces into component parts."""
        self.assertEqual(
            ["goog", "string", "startsWith"],
            namespace.GetNamespaceParts("goog.string.startsWith"),
        )

    def test_is_symbol_part_of_namespace(self):
        """Tests namespace membership checks."""
        self.assertTrue(
            namespace.IsSymbolPartOfNamespace("goog.string.startsWith", "goog.string")
        )

        self.assertFalse(
            namespace.IsSymbolPartOfNamespace("goog.string", "goog.string.startsWith")
        )

        self.assertTrue(namespace.IsSymbolPartOfNamespace("aaa.bbb.foo", "aaa.bbb.foo"))

    def test_get_prototype_property(self):
        """Tests extracting property names from prototype namespaces."""
        self.assertEqual("foo", namespace.GetPrototypeProperty("bar.prototype.foo"))
        self.assertRaises(AssertionError, lambda: namespace.GetPrototypeProperty("bar"))

    def test_get_symbol_parts_in_namespace(self):
        """Tests counting shared namespace prefix components."""
        self.assertEqual(
            0, namespace._get_symbol_parts_in_namespace(["aaa"], ["aaa", "bbb"])
        )
        self.assertEqual(
            1, namespace._get_symbol_parts_in_namespace(["aaa", "bbb"], ["aaa", "ccc"])
        )
