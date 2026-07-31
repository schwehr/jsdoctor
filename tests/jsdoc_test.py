"""Tests for the jsdoctor.jsdoc module."""

from jsdoctor import jsdoc


def test_process_comment() -> None:
    """Tests comment sectioning and flag parsing."""
    descriptions, flags = jsdoc.ProcessComment(_SCRIPT)

    assert flags == [
        ("@flag", "Thing thing"),
        ("@flag2", "More thing."),
        ("@flag3", "More thing and\nmore thing."),
        ("@flag4", "One last thing."),
    ]
    assert descriptions == ["This is a comment.", "End of thing."]


def test_split_sections() -> None:
    """Tests splitting comment blocks into section strings."""
    # pylint: disable-next=protected-access
    parts = list(jsdoc._yield_sections(_SCRIPT))
    assert parts == [
        "@flag Thing thing",
        "This is a comment.",
        "@flag2 More thing.\n@flag3 More thing and\nmore thing.",
        "End of thing.\n@flag4 One last thing.",
    ]


def test_match_flags() -> None:
    """Tests matching flag regex against comment text."""
    # pylint: disable-next=protected-access
    matches = jsdoc._match_flags(_SCRIPT)
    flags = [match.group("flag") for match in matches]
    assert flags == ["@flag", "@flag2", "@flag3", "@flag4"]


_SCRIPT = """\
@flag Thing thing


This is a comment.

@flag2 More thing.
@flag3 More thing and
more thing.

End of thing.
@flag4 One last thing.
"""
