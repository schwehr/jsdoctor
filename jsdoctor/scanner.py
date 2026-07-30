"""Regular expression scanners for JSDoc comments and Closure declarations."""

import re
from collections.abc import Iterator
from re import Match

_BASE_REGEX_STRING = "^\\s*goog\\.%s\\(\\s*['\"](.+)['\"]\\s*\\)"
_PROVIDE_REGEX = re.compile(_BASE_REGEX_STRING % "provide")
_REQUIRES_REGEX = re.compile(_BASE_REGEX_STRING % "require")


class NoIdentifierFoundError(Exception):
    """Exception raised when no identifier target is found following a comment."""


# pylint: disable-next=invalid-name
def YieldProvides(source: str) -> Iterator[str]:
    """Yields namespace strings provided by goog.provide calls in source.

    Args:
        source: JavaScript source code text.

    Yields:
        Provided namespace strings.
    """
    for line in source.splitlines():
        match = _PROVIDE_REGEX.match(line)
        if match:
            yield match.group(1)


# pylint: disable-next=invalid-name
def YieldRequires(source: str) -> Iterator[str]:
    """Yields namespace strings required by goog.require calls in source.

    Args:
        source: JavaScript source code text.

    Yields:
        Required namespace strings.
    """
    for line in source.splitlines():
        match = _REQUIRES_REGEX.match(line)
        if match:
            yield match.group(1)


# pylint: disable-next=invalid-name
def ExtractDocumentedSymbols(
    script: str,
) -> Iterator[tuple[Match[str], Match[str] | None]]:
    """Yields pairs of JSDoc comment match and identifier target match.

    Args:
        script: JavaScript source code text.

    Yields:
        Tuples of (comment_match, target_identifier_match).

    Raises:
        NoIdentifierFoundError: If a comment block has no target identifier.
    """
    for comment_match in FindJsDocComments(script):
        identifier_match = None

        if re.search(r"@fileoverview\b", comment_match.group()):
            # This is a file overview comment.
            pass

        else:
            identifier_match = FindCommentTarget(script, comment_match.end())
            if not identifier_match:
                raise NoIdentifierFoundError(
                    "Found no identifier for comment: " + comment_match.group()
                )

        yield comment_match, identifier_match


# pylint: disable-next=invalid-name
def FindJsDocComments(script: str) -> Iterator[Match[str]]:
    """Finds all JSDoc comment matches in JavaScript source code.

    Args:
        script: JavaScript source code text.

    Returns:
        An iterator of regex Match objects for JSDoc comments.
    """
    return re.finditer(r"/\*\*.*?\*/", script, re.DOTALL)


# pylint: disable-next=invalid-name
def FindCommentTarget(script: str, pos: int = 0) -> Match[str] | None:
    """Finds the identifier target immediately following a JSDoc comment.

    Args:
        script: JavaScript source code text.
        pos: Character offset in script to start searching.

    Returns:
        Regex match for the identifier target, or None if not found.
    """
    # Find an opening parenthesis or an identifier.
    # \w and $ should cover all valid identifiers.
    identifier_regex = re.compile(r"\(|(?:[$\w]+\s*\.\s*)*[$\w]+")
    return identifier_regex.search(script, pos=pos)


# pylint: disable-next=invalid-name
def StripWhitespace(original_string: str) -> str:
    """Strips all whitespace characters from a string.

    Args:
        original_string: The string to strip whitespace from.

    Returns:
        String with all whitespace characters removed.
    """
    return re.sub(r"\s*", "", original_string)


# pylint: disable-next=invalid-name
def ExtractTextFromJsDocComment(comment: str) -> str:
    """Strips JSDoc comment formatting markers (/**, */, leading asterisks).

    Args:
        comment: Raw JSDoc comment text.

    Returns:
        Cleaned text content of the JSDoc comment block.
    """
    comment = comment.strip()

    # Strip the leading "/**"
    assert comment.startswith("/**")
    comment = comment[3:]

    assert comment.endswith("*/")
    comment = comment[:-2]

    comment = comment.strip()
    lines = comment.splitlines(True)

    output_lines = []
    for line in lines:
        line = line.lstrip()
        if line.startswith("*"):
            line = line[1:].lstrip(" ")
            output_lines.append(line)

    return "".join(output_lines)
