"""Tests for jsdoctor.generator."""

from xml.dom import minidom

import pytest

from jsdoctor import generator, source, symboltypes


def test_make_text_node() -> None:
    """Tests creation of a DOM text node."""
    # pylint: disable-next=protected-access
    text_node = generator._make_text_node("hello world")
    assert isinstance(text_node, minidom.Text)
    assert text_node.data == "hello world"


def test_make_element() -> None:
    """Tests DOM element creation with and without text content."""
    # pylint: disable-next=protected-access
    elem1 = generator._make_element("div")
    assert isinstance(elem1, minidom.Element)
    assert elem1.tagName == "div"
    assert not elem1.childNodes

    # pylint: disable-next=protected-access
    elem2 = generator._make_element("p", "sample text")
    assert isinstance(elem2, minidom.Element)
    assert elem2.tagName == "p"
    assert len(elem2.childNodes) == 1
    assert isinstance(elem2.childNodes[0], minidom.Text)
    assert elem2.childNodes[0].data == "sample text"


def test_make_header() -> None:
    """Tests creation of an h2 header element."""
    # pylint: disable-next=protected-access
    header = generator._make_header("Header Title")
    assert header.tagName == "h2"
    assert len(header.childNodes) == 1
    assert isinstance(header.childNodes[0], minidom.Text)
    assert header.childNodes[0].data == "Header Title"


def test_make_link() -> None:
    """Tests creation of an anchor link element."""
    # pylint: disable-next=protected-access
    link = generator._make_link("Click Here", "https://example.com")
    assert link.tagName == "a"
    assert link.getAttribute("href") == "https://example.com"
    assert len(link.childNodes) == 1
    assert isinstance(link.childNodes[0], minidom.Text)
    assert link.childNodes[0].data == "Click Here"


def test_process_string() -> None:
    """Tests string processing with URL linkification and HTML parsing."""
    # pylint: disable-next=protected-access
    fragment = generator._process_string("Visit https://google.com for info.")
    assert isinstance(fragment, minidom.DocumentFragment)
    xml_output = "".join(child.toxml() for child in fragment.childNodes)
    assert "https://google.com" in xml_output
    assert "<a " in xml_output


def test_is_static_helpers() -> None:
    """Tests _IsStatic and _IsNotStatic helper functions."""
    symbol_static = source.Symbol("foo.bar", 0, 10)
    symbol_static.static = True
    # pylint: disable-next=protected-access
    assert generator._is_static(symbol_static) is True
    # pylint: disable-next=protected-access
    assert generator._is_not_static(symbol_static) is False

    symbol_instance = source.Symbol("foo.bar", 0, 10)
    symbol_instance.static = False
    # pylint: disable-next=protected-access
    assert generator._is_static(symbol_instance) is False
    # pylint: disable-next=protected-access
    assert generator._is_not_static(symbol_instance) is True


def test_get_symbols_of_type() -> None:
    """Tests filtering symbols by symbol type."""
    sym1 = source.Symbol("foo.Func", 0, 10)
    sym1.type = symboltypes.FUNCTION

    sym2 = source.Symbol("foo.Class", 0, 10)
    sym2.type = symboltypes.CONSTRUCTOR

    symbols = [sym1, sym2]

    # pylint: disable-next=protected-access
    funcs = generator._get_symbols_of_type(symbols, symboltypes.FUNCTION)
    assert funcs == [sym1]

    # pylint: disable-next=protected-access
    ctors = generator._get_symbols_of_type(symbols, symboltypes.CONSTRUCTOR)
    assert ctors == [sym2]

    # pylint: disable-next=protected-access
    enums = generator._get_symbols_of_type(symbols, symboltypes.ENUM)
    assert enums == []


def test_yield_param_flags() -> None:
    """Tests extracting @param flags from an iterable of flags."""
    flag_param = source.Flag("@param", "{string} name User name.")
    flag_return = source.Flag("@return", "{boolean}")
    flag_private = source.Flag("@private", "")

    param_flags = list(
        # pylint: disable-next=protected-access
        generator._yield_param_flags([flag_param, flag_return, flag_private])
    )
    assert param_flags == [flag_param]


def test_get_param_string() -> None:
    """Tests formatting of parameter flag strings."""
    flag_param = source.Flag("@param", "{number} count Item count.")
    # pylint: disable-next=protected-access
    param_str = generator._get_param_string(flag_param)
    assert param_str == "{number} count"


def test_get_return_flag_and_string() -> None:
    """Tests extraction and formatting of return flags."""
    flag_param = source.Flag("@param", "{string} x")
    flag_return = source.Flag("@return", "{string} Result string.")

    # pylint: disable-next=protected-access
    ret_flag = generator._get_return_flag([flag_param, flag_return])
    assert ret_flag == flag_return

    # pylint: disable-next=protected-access
    no_ret = generator._get_return_flag([flag_param])
    assert no_ret is None

    # pylint: disable-next=protected-access
    ret_str = generator._get_return_string(flag_return)
    assert ret_str == "{string}"


def test_get_return_flag_duplicate_raises() -> None:
    """Tests that having more than one @return flag raises an AssertionError."""
    flag1 = source.Flag("@return", "{string}")
    flag2 = source.Flag("@return", "{number}")
    with pytest.raises(
        AssertionError, match="There should not be more than 1 @return flag."
    ):
        # pylint: disable-next=protected-access
        generator._get_return_flag([flag1, flag2])


def test_generate_documents_and_html_docs() -> None:
    """Tests GenerateDocuments and GenerateHtmlDocs with a realistic source script."""
    script = """
goog.provide('my.namespace');

/**
 * Creates a new MyClass instance.
 * @constructor
 */
my.namespace.MyClass = function() {};

/**
 * Interface definition.
 * @interface
 */
my.namespace.MyInterface = function() {};

/**
 * Enum definition.
 * @enum {string}
 */
my.namespace.MyEnum = {
  FOO: 'foo'
};

/**
 * Performs an action.
 * @param {string} name User name.
 * @param {number} count Count value.
 * @return {boolean} True if successful.
 */
my.namespace.MyClass.prototype.doSomething = function(name, count) {};

/**
 * Helper function.
 * @private
 */
my.namespace.MyClass.prototype.secretHelper = function() {};

/**
 * Factory method.
 * @param {string} id Unique identifier.
 * @return {!my.namespace.MyClass} Created instance.
 */
my.namespace.MyClass.create = function(id) {};

/**
 * No params static method.
 */
my.namespace.MyClass.noParams = function() {};

/**
 * Instance property.
 * @type {number}
 */
my.namespace.MyClass.prototype.myProp;

/**
 * Static property.
 * @type {string}
 */
my.namespace.MyClass.STATIC_PROP = 'value';
"""
    src = source.ScanScript(script)
    symbols = list(src.symbols)
    namespace_map = {"my.namespace": symbols}

    # Test GenerateDocuments
    docs = list(generator.GenerateDocuments(namespace_map))
    assert len(docs) == 1
    filename, doc = docs[0]
    assert filename == "my.namespace.html"
    assert isinstance(doc, minidom.Document)

    # Test GenerateHtmlDocs
    html_docs = list(generator.GenerateHtmlDocs(namespace_map))
    assert len(html_docs) == 1
    out_filename, content_bytes = html_docs[0]
    assert out_filename == "my.namespace.html"
    assert isinstance(content_bytes, bytes)

    content = content_bytes.decode("utf-8")
    assert "<h1>my.namespace</h1>" in content
    assert "Constructor" in content
    assert "Interface" in content
    assert "Enumerations" in content
    assert "Public instance method summary" in content
    assert "Public static method summary" in content
    assert "Instance methods" in content
    assert "Static methods" in content
    assert "Instance properties" in content
    assert "Static properties" in content
    assert "doSomething" in content
    assert "secretHelper" in content
    assert "STATIC_PROP" in content
