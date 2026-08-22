"""Data structures and source parsing orchestration for JavaScript files."""

import logging
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from . import flags, jsdoc, namespace, scanner, symboltypes


@dataclass(eq=False)
class Source:
    """Represents a parsed JavaScript source file and its extracted symbols.

    Attributes:
        script: Raw JavaScript source code text.
        path: Optional file path to the source file.
        provides: Set of provided namespace strings.
        requires: Set of required namespace strings.
        symbols: Set of extracted Symbol objects.
        filecomment: Optional top-level file JSDoc comment.
    """

    script: str
    path: str | None = None
    provides: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)
    symbols: set[Symbol] = field(default_factory=set)  # pyrefly: ignore[unbound-name]
    filecomment: Comment | None = None  # pyrefly: ignore[unbound-name]

    def __str__(self) -> str:
        source_string = super().__str__()

        if self.path:
            source_string += " " + self.path

        return source_string


@dataclass(eq=False)
class Symbol:
    """Represents a documented JavaScript identifier target.

    Attributes:
        identifier: JavaScript target identifier string.
        start: Starting character position in source script.
        end: Ending character position in source script.
        source: Optional parent Source object.
        comment: Optional associated Comment object.
        namespace: Optional namespace name.
        property: Optional property name.
        type: Optional symbol classification type.
        static: Optional flag indicating if symbol is static.
    """

    identifier: str
    start: int
    end: int
    source: Source | None = None
    comment: Comment | None = None
    namespace: str | None = None
    property: str | None = None
    type: str | None = None
    static: bool | None = None

    def __str__(self) -> str:
        symbol_string = super().__str__()

        symbol_string += " " + self.identifier

        if self.source:
            symbol_string += " " + str(self.source)

        return symbol_string


@dataclass
class Flag:
    """Represents a JSDoc flag tag within a comment.

    Attributes:
        name: Flag tag name (e.g. '@param', '@return').
        text: Associated text for the flag tag.
    """

    name: str
    text: str

    def __post_init__(self) -> None:
        assert self.name in flags.ALL_FLAGS, f"Unrecognized flag: {self.name}"


@dataclass(eq=False)
class Comment:
    """Represents a parsed JSDoc comment block with description and flags.

    Attributes:
        text: Raw JSDoc comment block text.
        start: Starting character index of comment in source.
        end: Ending character index of comment in source.
        flags: List of parsed Flag objects.
        description_sections: List of parsed description text sections.
    """

    text: str
    start: int
    end: int
    flags: list[Flag] = field(default_factory=list, init=False)
    description_sections: list[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        description_sections, parsed_flags = _get_description_and_flags(self.text)
        self.description_sections = description_sections
        self.flags = parsed_flags


def _get_description_and_flags(text: str) -> tuple[list[str], list[Flag]]:
    description_sections, flag_pairs = jsdoc.ProcessComment(text)
    parsed_flags = [Flag(name, text) for name, text in flag_pairs]
    return description_sections, parsed_flags


def _is_symbol_part_of_provided_namespaces(
    symbol: str, provided_namespaces: set[str]
) -> bool:
    for ns in provided_namespaces:
        if namespace.IsSymbolPartOfNamespace(symbol, ns):
            return True
    return False


def _is_ignorable_identifier(identifier_match: re.Match) -> bool:
    # Find the first non-whitespace character after the identifier.
    regex = re.compile(r"[\S]")
    match = regex.search(identifier_match.string, pos=identifier_match.end())
    if match:
        first_character = match.group()
        if first_character in ["(", "["]:
            # This is a method call or a bracket-notation property access. Ignore.
            return True

    return False


class NamespaceNotFoundError(Exception):
    """Exception raised when a symbol does not belong to any provided namespace."""


# TODO(nanaze): In the future this could farm out to a formal parser like
# Esprima to correctly identify comments. Regexing seems to work OK for now.
def _yield_symbols(
    match_pairs: Iterable[tuple[re.Match[str], re.Match[str] | None]],
    provided_namespaces: set[str],
) -> Iterator[Symbol]:
    for comment_match, identifier_match in match_pairs:
        if not identifier_match:
            continue
        comment_text = scanner.ExtractTextFromJsDocComment(comment_match.group())
        comment = Comment(comment_text, comment_match.start(), comment_match.end())

        # TODO(schwehr): What was this supposed to do?
        # if not identifier_match:
        #   assert not source.filecomment, '@fileoverview comment made more than once'
        #   source.filecomment = comment
        #   continue

        if _is_ignorable_identifier(identifier_match):
            # This is JsDoc on a method call, most likely a type cast of a return value.
            # Ignore.
            continue

        if identifier_match.group() == "(":
            # This comment targeted a parenthetical and can be ignored.
            continue

        # TODO(nanaze): Identify scoped variables and expand identifiers.
        identifier = scanner.StripWhitespace(identifier_match.group())

        # TODO(nanaze): catch this. properties, make sure not static
        if identifier.startswith("this."):
            logging.info(
                'Skipping identifier. Ignoring "this." properties for now. %s',
                identifier,
            )
            continue

        # Ignore symbols that are not part of the provided namespace.
        if not _is_symbol_part_of_provided_namespaces(identifier, provided_namespaces):
            logging.info(
                "Skipping identifier. Not part of provided namespace. %s",
                identifier,
            )
            continue

        symbol = Symbol(identifier, identifier_match.start(), identifier_match.end())
        symbol.comment = comment

        # Determine symbol type
        symbol.type = symboltypes.DetermineSymbolType(symbol)

        # Identify the namespace for this symbol.
        closest_namespace = namespace.GetClosestNamespaceForSymbol(
            identifier, provided_namespaces
        )

        if not closest_namespace:
            raise NamespaceNotFoundError("No namespace found " + identifier)

        symbol.namespace = closest_namespace

        # Note the property name
        if namespace.IsPrototypeProperty(identifier):
            symbol.property = namespace.GetPrototypeProperty(identifier)
            symbol.static = False
        else:
            symbol.static = True

        yield symbol


# pylint: disable-next=invalid-name
def ScanScript(script: str, path: str | None = None) -> Source:
    """Parses JavaScript script text and returns a populated Source instance.

    Args:
        script: JavaScript source code text.
        path: Optional file path of the source file.

    Returns:
        A Source instance with populated provides, requires, and symbols.
    """
    source = Source(script, path)
    source.provides.update(set(scanner.YieldProvides(script)))
    source.requires.update(set(scanner.YieldRequires(script)))

    match_pairs = scanner.ExtractDocumentedSymbols(script)
    for symbol in _yield_symbols(match_pairs, source.provides):
        symbol.source = source
        source.symbols.add(symbol)

    return source
