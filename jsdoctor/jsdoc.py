"""Parsing and sectioning logic for JSDoc comment blocks."""

import re
from collections.abc import Iterator


# pylint: disable-next=invalid-name
def ProcessComment(comment_text: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Parses a JSDoc comment text into description sections and raw flag tuples.

    Args:
        comment_text: Raw JSDoc comment text block.

    Returns:
        A tuple of (description_list, flag_tuples_list).
    """
    descriptions = []
    flags = []

    for section_text in _yield_sections(comment_text):
        description, section_flags = _process_comment_section(section_text)

        if description:
            descriptions.append(description)

        flags.extend(section_flags)

    return descriptions, flags


def _process_comment_section(section_text: str) -> tuple[str, list[tuple[str, str]]]:
    remaining_text = section_text
    flags: list[tuple[str, str]] = []

    matches = list(_match_flags(section_text))
    matches.reverse()

    # A flag is itself and whatever text appears behind it (until the next flag
    # or the end of a section).
    for flag_match in matches:
        flag_name = flag_match.group("flag")
        flag_text = remaining_text[flag_match.end() :].strip()

        flags.insert(0, (flag_name, flag_text))

        remaining_text = remaining_text[0 : flag_match.start()]

    # The description is whatever wasn't part of a flag.
    description = remaining_text

    return description, flags


def _match_flags(text: str) -> Iterator[re.Match]:
    return re.finditer(r"(?:\s|\A)(?P<flag>@\w+)\b", text)


def _yield_sections(comment_text: str) -> Iterator[str]:
    assert "\r" not in comment_text, "Non-UNIX strings not supported for now"
    parts = comment_text.split("\n\n")

    for part in parts:
        part = part.strip()

        # skip empty strings
        if part:
            yield part
