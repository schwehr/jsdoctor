from __future__ import annotations

import logging
import re
from typing import Iterable, Iterator

from . import flags
from . import jsdoc
from . import namespace
from . import scanner
from . import symboltypes


class Source:

  script: str
  path: str | None
  provides: set[str]
  requires: set[str]
  symbols: set[Symbol]
  filecomment: Comment | None

  def __init__(self, script: str, path: str | None = None):
    self.script = script
    self.path = path

    self.provides = set()
    self.requires = set()
    self.symbols = set()
    self.filecomment = None

  def __str__(self) -> str:
    source_string = super().__str__()

    if self.path:
      source_string += ' ' + self.path

    return source_string


class Symbol:

  identifier: str
  start: int
  end: int
  source: Source | None
  comment: Comment | None
  namespace: str | None
  property: str | None
  type: str | None
  static: bool | None

  def __init__(self, identifier: str, start: int, end: int) -> None:
    self.identifier = identifier
    self.start = start
    self.end = end
    self.source = None
    self.comment = None
    self.namespace = None
    self.property = None
    self.type = None
    self.static = None

  def __str__(self) -> str:
    symbol_string = super().__str__()

    symbol_string += ' ' + self.identifier

    if self.source:
      symbol_string += ' ' + str(self.source)

    return symbol_string


class Comment:

  text: str
  start: int
  end: int
  flags: list[Flag]
  description_sections: list[str]

  def __init__(self, text: str, start: int, end: int) -> None:

    self.text = text
    self.start = start
    self.end = end

    description_sections, flags = _GetDescriptionAndFlags(text)
    self.description_sections = description_sections
    self.flags = flags


class Flag:

  name: str
  text: str

  def __init__(self, name: str, text: str):

    assert name in flags.ALL_FLAGS, 'Unrecognized flag: ' + name

    self.name = name
    self.text = text


def _GetDescriptionAndFlags(text: str) -> tuple[list[str], list[Flag]]:
  description_sections, flag_pairs = jsdoc.ProcessComment(text)
  flags = [Flag(name, text) for name, text in flag_pairs]
  return description_sections, flags


def _IsSymbolPartOfProvidedNamespaces(symbol: str, provided_namespaces: set[str]) -> bool:
  for ns in provided_namespaces:
    if namespace.IsSymbolPartOfNamespace(symbol, ns):
      return True
  return False


def _IsIgnorableIdentifier(identifier_match: re.Match) -> bool:

  # Find the first non-whitespace character after the identifier.
  regex = re.compile(r'[\S]')
  match = regex.search(identifier_match.string, pos=identifier_match.end())
  if match:
    first_character = match.group()
    if first_character in ['(', '[']:
      # This is a method call or a bracket-notation property access. Ignore.
      return True

  return False


class NamespaceNotFoundError(Exception):
  pass


# TODO(nanaze): In the future this could farm out to a formal parser like
# Esprima to correctly identify comments. Regexing seems to work OK for now.
def _YieldSymbols(
    match_pairs: Iterable[tuple[re.Match, re.Match]],
    provided_namespaces: set[str],
) -> Iterator[Symbol]:
  for comment_match, identifier_match in match_pairs:
    comment_text = scanner.ExtractTextFromJsDocComment(comment_match.group())
    comment = Comment(comment_text, comment_match.start(), comment_match.end())

    # TODO(schwehr): What was this supposed to do?
    # if not identifier_match:
    #   assert not source.filecomment, '@fileoverview comment made more than once'
    #   source.filecomment = comment
    #   continue

    if _IsIgnorableIdentifier(identifier_match):
      # This is JsDoc on a method call, most likely a type cast of a return value.
      # Ignore.
      continue

    if identifier_match.group() == '(':
      # This comment targeted a parenthetical and can be ignored.
      continue

    # TODO(nanaze): Identify scoped variables and expand identifiers.
    identifier = scanner.StripWhitespace(identifier_match.group())

    # TODO(nanaze): catch this. properties, make sure not static
    if identifier.startswith('this.'):
      logging.info('Skipping identifier. Ignoring "this." properties for now. ' + identifier)
      continue

    # Ignore symbols that are not part of the provided namespace.
    if not _IsSymbolPartOfProvidedNamespaces(identifier, provided_namespaces):
      logging.info('Skipping identifier. Not part of provided namespace. ' + identifier)
      continue

    symbol = Symbol(identifier, identifier_match.start(), identifier_match.end())
    symbol.comment = comment

    # Determine symbol type
    symbol.type = symboltypes.DetermineSymbolType(symbol)

    # Identify the namespace for this symbol.
    closest_namespace = namespace.GetClosestNamespaceForSymbol(
        identifier, provided_namespaces)

    if not closest_namespace:
      raise NamespaceNotFoundError('No namespace found ' + identifier)

    symbol.namespace = closest_namespace

    # Note the property name
    if namespace.IsPrototypeProperty(identifier):
      symbol.property = namespace.GetPrototypeProperty(identifier)
      symbol.static = False
    else:
      symbol.static = True

    yield symbol


def ScanScript(script: str, path: str | None = None) -> Source:
  source = Source(script, path)
  source.provides.update(set(scanner.YieldProvides(script)))
  source.requires.update(set(scanner.YieldRequires(script)))

  match_pairs = scanner.ExtractDocumentedSymbols(script)
  for symbol in _YieldSymbols(match_pairs, source.provides):
    symbol.source = source
    source.symbols.add(symbol)

  return source
