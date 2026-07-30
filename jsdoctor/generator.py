"""HTML document generator for namespace API reference documentation."""

from collections.abc import Iterable, Iterator, Mapping
from typing import Any
from xml.dom import minidom

import html5lib

from . import flags, linkify, symboltypes


# pylint: disable-next=invalid-name
def GenerateHtmlDocs(
    namespace_map: Mapping[str, Iterable[Any]],
) -> Iterator[tuple[str, bytes]]:
    """Generates HTML document filename and bytes pairs for each namespace.

    Args:
        namespace_map: Mapping from namespace string to list of symbols.

    Yields:
        Tuples of (filename, html_bytes).
    """
    for filepath, document in GenerateDocuments(namespace_map):
        assert document.documentElement is not None
        content = document.documentElement.toxml("utf-8")
        yield filepath, content


# pylint: disable-next=invalid-name
def GenerateDocuments(
    namespace_map: Mapping[str, Iterable[Any]],
) -> Iterator[tuple[str, minidom.Document]]:
    """Generates DOM documents for each namespace in namespace_map.

    Args:
        namespace_map: Mapping from namespace string to list of symbols.

    Yields:
        Tuples of (filename, minidom.Document).
    """
    for namespace, symbols in namespace_map.items():
        filename = f"{namespace}.html"
        yield filename, _generate_document(namespace, symbols)


def _process_string(content: str) -> minidom.DocumentFragment:
    content = linkify.LinkifyWebUrls(content)
    return html5lib.parseFragment(content, treebuilder="dom")


def _make_text_node(content: str) -> minidom.Text:
    text = minidom.Text()
    text.data = content
    return text


def _make_header(content: str | None = None) -> minidom.Element:
    return _make_element("h2", content)


def _make_element(tagname: str, content: str | None = None) -> minidom.Element:
    element = minidom.Element(tagname)

    if content:
        element.appendChild(_make_text_node(content))

    return element


def _is_static(symbol: Any) -> bool:
    return bool(symbol.static)


def _is_not_static(symbol: Any) -> bool:
    return not _is_static(symbol)


def _get_symbols_of_type(symbols: Iterable[Any], symbol_type: Any) -> list[Any]:
    return [symbol for symbol in symbols if symbol.type == symbol_type]


def _generate_document(namespace: str, symbols: Iterable[Any]) -> minidom.Document:
    dom = minidom.getDOMImplementation()
    assert dom is not None  # For pytype.
    doc = dom.createDocument(None, "html", None)

    body = doc.createElement("body")
    assert doc.documentElement is not None
    doc.documentElement.appendChild(body)

    for elem in _generate_content(namespace, symbols):
        body.appendChild(elem)

    return doc


def _add_symbol_description(node_list: minidom.NodeList, symbol: Any) -> None:
    node_list.append(_make_element("h3", symbol.identifier))
    for section in symbol.comment.description_sections:
        elem = _process_string(section)
        p = _make_element("p")
        node_list.append(p)
        p.appendChild(elem)


def _make_link(text: str, href: str) -> minidom.Element:
    a = _make_element("a", text)
    a.setAttribute("href", href)
    return a


def _yield_param_flags(comment_flags: Iterable[Any]) -> Iterator[Any]:
    for flag in comment_flags:
        if flag.name == "@param":
            yield flag


def _get_param_string(flag: Any) -> str:
    assert flag.name == "@param"
    name, type_str, _ = flags.ParseParameterDescription(flag.text)
    return f"{{{type_str}}} {name}"


def _get_return_flag(comment_flags: Iterable[Any]) -> Any | None:
    return_flags = list(filter(lambda flag: flag.name == "@return", comment_flags))
    assert len(return_flags) <= 1, "There should not be more than 1 @return flag."

    if not return_flags:
        return None

    return return_flags[0]


def _get_return_string(flag: Any) -> str:
    assert flag.name == "@return"
    type_str, _ = flags.ParseReturnDescription(flag.text)
    return f"{{{type_str}}}"


def _make_function_code_element(name: str, function: Any) -> minidom.Element:
    code = _make_element("code")
    code.appendChild(_make_link(name, "#" + name))

    param_flags = list(_yield_param_flags(function.comment.flags))
    param_strings = [_get_param_string(flag) for flag in param_flags]
    param_line = ", ".join(param_strings)

    text_node = _make_text_node(f"({param_line})")
    code.appendChild(text_node)

    return_flag = _get_return_flag(function.comment.flags)
    if return_flag:
        code.appendChild(_make_text_node(" : "))
        code.appendChild(_make_text_node(_get_return_string(return_flag)))
    return code


def _make_function_summary_list(functions: Iterable[Any]) -> minidom.Element:
    summary_list = _make_element("dl")

    for function in functions:
        summary_term = _make_element("dt")
        summary_list.appendChild(summary_term)

        if _is_static(function):
            name = function.identifier
        else:
            name = function.property

        code = _make_function_code_element(name, function)
        summary_term.appendChild(code)

        summary_definition = _make_element("dd")
        summary_term.appendChild(summary_definition)

        if function.comment.description_sections:
            desc = function.comment.description_sections[0]
            summary_definition.appendChild(_process_string(desc))

    return summary_list


def _add_function_description(node_list: minidom.NodeList, function: Any) -> None:
    header = _make_element("h3", function.identifier)
    header.setAttribute("id", function.identifier)
    node_list.append(header)

    # Draw function signature.
    param_flags = list(_yield_param_flags(function.comment.flags))

    function_interface = ""
    function_interface += flags.GetVisibility(function.comment.flags) + " "
    function_interface += f"{function.identifier}("

    # Draw parameters.
    if param_flags:
        for index, flag in enumerate(param_flags):
            function_interface += f"\n  {_get_param_string(flag)}"

            # If this is not the last parameter, draw a comma.
            if index != (len(param_flags) - 1):
                function_interface += ","
            else:
                function_interface += "\n"

    function_interface += ")"

    # Draw return.
    return_flag = _get_return_flag(function.comment.flags)
    if return_flag:
        function_interface += " : " + _get_return_string(return_flag)

    node_list.append(_make_element("pre", function_interface))

    # Parameter list.
    if param_flags:
        node_list.append(_make_element("h4", "Parameters:"))

        param_list = _make_element("dl")
        node_list.append(param_list)
        for flag in param_flags:
            name, type_str, desc = flags.ParseParameterDescription(flag.text)
            term = _make_element("dt", name)
            param_list.appendChild(term)

            definition = _make_element("dd")

            code_type = _make_element("code", f"{{{type_str}}}")
            definition.appendChild(code_type)
            definition.appendChild(_make_text_node(" "))
            definition.appendChild(_process_string(desc))
            term.appendChild(definition)

    if return_flag:
        node_list.append(_make_element("h4", "Returns:"))
        return_paragraph = _make_element("p")
        node_list.append(return_paragraph)

        type_str, desc = flags.ParseReturnDescription(return_flag.text)
        code_type = _make_element("code", f"{{{type_str}}}")
        return_paragraph.appendChild(code_type)
        return_paragraph.appendChild(_make_text_node(" "))
        return_paragraph.appendChild(_process_string(desc))

    # Add description paragraphs.
    for section in function.comment.description_sections:
        section_paragraph = _make_element("p")
        section_paragraph.appendChild(_process_string(section))
        node_list.append(section_paragraph)


def _generate_content(namespace: str, symbols: Iterable[Any]) -> minidom.NodeList:
    node_list = minidom.NodeList()

    node_list.append(_make_element("h1", namespace))

    sorted_symbols = sorted(symbols, key=lambda symbol: symbol.identifier)

    # Constructor.
    constructor_symbols = _get_symbols_of_type(sorted_symbols, symboltypes.CONSTRUCTOR)

    if constructor_symbols:
        node_list.append(_make_element("h2", "Constructor"))
        for constructor in constructor_symbols:
            _add_symbol_description(node_list, constructor)

    # Interface.
    interface_symbols = _get_symbols_of_type(sorted_symbols, symboltypes.INTERFACE)

    if interface_symbols:
        node_list.append(_make_element("h2", "Interface"))
        for interface in interface_symbols:
            _add_symbol_description(node_list, interface)

    instance_methods = list(
        filter(
            _is_not_static, _get_symbols_of_type(sorted_symbols, symboltypes.FUNCTION)
        )
    )

    instance_properties = list(
        filter(
            _is_not_static, _get_symbols_of_type(sorted_symbols, symboltypes.PROPERTY)
        )
    )

    static_functions = list(
        filter(_is_static, _get_symbols_of_type(sorted_symbols, symboltypes.FUNCTION))
    )

    public_instance_methods = list(
        filter(
            lambda m: flags.GetVisibility(m.comment.flags) == flags.PUBLIC,
            instance_methods,
        )
    )
    if public_instance_methods:
        node_list.append(_make_element("h2", "Public instance method summary"))
        node_list.append(_make_function_summary_list(public_instance_methods))

    public_static_methods = list(
        filter(
            lambda m: flags.GetVisibility(m.comment.flags) == flags.PUBLIC,
            static_functions,
        )
    )
    if static_functions:
        node_list.append(_make_element("h2", "Public static method summary"))
        node_list.append(_make_function_summary_list(public_static_methods))

    # Enumerations.
    enum_symbols = _get_symbols_of_type(sorted_symbols, symboltypes.ENUM)

    if enum_symbols:
        node_list.append(_make_element("h2", "Enumerations"))
        for enum_symbol in enum_symbols:
            _add_symbol_description(node_list, enum_symbol)

    if instance_methods:
        node_list.append(_make_element("h2", "Instance methods"))
        for method in instance_methods:
            _add_function_description(node_list, method)
            node_list.append(_make_element("hr"))

    if instance_properties:
        node_list.append(_make_element("h2", "Instance properties"))
        for prop in instance_properties:
            _add_symbol_description(node_list, prop)
            node_list.append(_make_element("hr"))

    if static_functions:
        node_list.append(_make_element("h2", "Static methods"))
        node_list.append(_make_element("hr"))
        for function in static_functions:
            _add_function_description(node_list, function)
            node_list.append(_make_element("hr"))

    static_properties = list(
        filter(_is_static, _get_symbols_of_type(sorted_symbols, symboltypes.PROPERTY))
    )
    if static_properties:
        node_list.append(_make_element("h2", "Static properties"))
        for prop in static_properties:
            _add_symbol_description(node_list, prop)
            node_list.append(_make_element("hr"))

    return node_list
