"""Definitions and sets for supported JSDoc flags."""

import re
from collections.abc import Iterable
from typing import Any

BASE_FLAGS = frozenset(["@provideGoog"])

JSDOC_FLAGS = frozenset(["@suppress"])

FILE_FLAGS = frozenset(["@author", "@fileoverview", "@see", "@license", "@visibility"])

FUNCTION_FLAGS = frozenset(
    [
        "@param",
        "@return",
        "@template",
        "@deprecated",
        "@throws",
        "@see",
        "@override",
    ]
)

VISIBILITY_FLAGS = frozenset(
    [
        # Everything public by default
        "@protected",
        "@private",
    ]
)

INSTANTIABLE_FLAGS = frozenset(
    [
        "@constructor",
        "@extends",
        "@implements",
        "@see",
    ]
)

TYPEDEF_FLAGS = frozenset(["@typedef"])

PROPERTY_FLAGS = frozenset(
    ["@const", "@define", "@enum", "@struct", "@type", "@inheritDoc", "@export"]
)

INTERFACE_FLAGS = frozenset(["@interface", "@extends"])

COMPILER_FLAGS = frozenset(
    [
        "@nocompile",
        "@preserveTry",
    ]
)

# TODO(nanaze): File.
MISC_FLAGS = frozenset(
    ["@desc", "@supported", "@hidden", "@final", "@idGenerator", "@this"]
)

all_flags: frozenset[str] = frozenset(
    MISC_FLAGS
    | BASE_FLAGS
    | COMPILER_FLAGS
    | JSDOC_FLAGS
    | FILE_FLAGS
    | FUNCTION_FLAGS
    | INTERFACE_FLAGS
    | INSTANTIABLE_FLAGS
    | PROPERTY_FLAGS
    | TYPEDEF_FLAGS
    | VISIBILITY_FLAGS
)

ALL_FLAGS = frozenset(all_flags)


# pylint: disable-next=invalid-name
def ParseParameterDescription(desc: str) -> tuple[str, str, str]:
    """Parses a JSDoc @param flag description into name, type, and text.

    Args:
        desc: The raw text following @param.

    Returns:
        A tuple of (name, type, text).

    Raises:
        ValueError: If the description cannot be parsed into a parameter.
    """
    match = re.match(
        r"^\s*\{(?P<type>.*?)\}\s+(?P<name>\w+)(?P<desc>.*)$",
        desc,
        re.DOTALL | re.MULTILINE,
    )
    if not match:
        raise ValueError(f"Could not parse flag description: {desc}")
    return (
        match.group("name").strip(),
        match.group("type").strip(),
        match.group("desc").strip(),
    )


# pylint: disable-next=invalid-name
def ParseReturnDescription(desc: str) -> tuple[str, str]:
    """Parses a JSDoc @return flag description into type and text.

    Args:
        desc: The raw text following @return.

    Returns:
        A tuple of (type, text).

    Raises:
        ValueError: If the description cannot be parsed into a return declaration.
    """
    match = re.match(
        r"^\s*{(?P<type>.*?)\}(?P<desc>.*)$", desc, re.DOTALL | re.MULTILINE
    )
    if not match:
        raise ValueError(f"Could not parse flag description: {desc}")
    return (match.group("type").strip(), match.group("desc").strip())


PUBLIC = "public"
PROTECTED = "protected"
PRIVATE = "private"


# pylint: disable-next=invalid-name
def GetVisibility(flags: Iterable[Any]) -> str:
    """Returns one of PUBLIC, PROTECTED, or PRIVATE."""

    flag_names = [flag.name for flag in flags]
    if "@private" in flag_names:
        return PRIVATE

    if "@protected" in flag_names:
        return PROTECTED

    return PUBLIC


# pylint: disable-next=invalid-name
def GetSymbolType(flags: Iterable[Any]) -> str | None:
    """Extracts the symbol data type from a collection of flags if present.

    Args:
        flags: Collection of Flag objects.

    Returns:
        The extracted type string, or None if no type is found.
    """
    for flag in flags:
        if flag.name in ["@type", "@const", "@protected", "@private"]:
            flag_type = MaybeParseTypeFromDescription(flag.text)
            if flag_type:
                return flag_type

    return None


# pylint: disable-next=invalid-name
def MaybeParseTypeFromDescription(desc: str) -> str | None:
    """Extracts a type string enclosed in curly braces from a flag description.

    Args:
        desc: The flag description text.

    Returns:
        The extracted type string, or None if no type braces are matched.
    """
    match = re.match(r"^\s*{(?P<type>.*?)}", desc, re.DOTALL | re.MULTILINE)
    if not match:
        return None

    return match.group("type")
