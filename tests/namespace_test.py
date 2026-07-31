"""Tests for the jsdoctor.namespace module."""

import pytest

from jsdoctor import namespace


def test_prototype_property() -> None:
    """Tests identifying prototype property namespaces."""
    assert namespace.IsPrototypeProperty("foo.prototype.yes")
    assert not namespace.IsPrototypeProperty("foo.prototype.yes.no")
    assert not namespace.IsPrototypeProperty("foo.bar.baz")


def test_nearest_namespace() -> None:
    """Tests finding closest matching namespace for symbols."""
    closest = namespace.GetClosestNamespaceForSymbol(
        "aaa.bbb.ccc", {"aaa.bbb.ccc.ddd", "aaa.bbb.ccc.eee"}
    )
    assert closest is None

    closest = namespace.GetClosestNamespaceForSymbol(
        "aaa.bbb.ccc", {"aaa.bbb", "aaa.bbb.ccc.ddd"}
    )
    assert closest == "aaa.bbb"

    closest = namespace.GetClosestNamespaceForSymbol(
        "goog.string.startsWith", {"goog.string", "goog.string.Unicode"}
    )
    assert closest == "goog.string"


def test_get_namespace_parts() -> None:
    """Tests splitting namespaces into component parts."""
    assert namespace.GetNamespaceParts("goog.string.startsWith") == [
        "goog",
        "string",
        "startsWith",
    ]


def test_is_symbol_part_of_namespace() -> None:
    """Tests namespace membership checks."""
    assert namespace.IsSymbolPartOfNamespace("goog.string.startsWith", "goog.string")

    assert not namespace.IsSymbolPartOfNamespace(
        "goog.string", "goog.string.startsWith"
    )

    assert namespace.IsSymbolPartOfNamespace("aaa.bbb.foo", "aaa.bbb.foo")


def test_get_prototype_property() -> None:
    """Tests extracting property names from prototype namespaces."""
    assert namespace.GetPrototypeProperty("bar.prototype.foo") == "foo"
    with pytest.raises(AssertionError):
        namespace.GetPrototypeProperty("bar")


def test_get_symbol_parts_in_namespace() -> None:
    """Tests counting shared namespace prefix components."""
    # pylint: disable-next=protected-access
    assert namespace._get_symbol_parts_in_namespace(["aaa"], ["aaa", "bbb"]) == 0
    # pylint: disable-next=protected-access
    assert namespace._get_symbol_parts_in_namespace(["aaa", "bbb"], ["aaa", "ccc"]) == 1
