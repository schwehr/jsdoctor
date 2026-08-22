"""Classification logic for determining JavaScript symbol types."""

import typing

if typing.TYPE_CHECKING:
    from . import source

CONSTRUCTOR = "constructor"
INTERFACE = "interface"
ENUM = "enum"
FUNCTION = "function"
PROPERTY = "property"


def _comment_has_flag(comment: source.Comment, flag_name: str) -> bool:
    assert flag_name.startswith("@"), "flag name should start with @"
    for flag in comment.flags:
        if flag.name == flag_name:
            return True
    return False


# pylint: disable-next=invalid-name
def DetermineSymbolType(symbol: source.Symbol) -> str:
    """Determines the symbol type (CONSTRUCTOR, INTERFACE, ENUM, FUNCTION, PROPERTY).

    Args:
        symbol: The Symbol instance to classify.

    Returns:
        The classified symbol type string constant.
    """
    comment = symbol.comment
    assert comment, "Expected to have comment"

    if _comment_has_flag(comment, "@constructor"):
        return CONSTRUCTOR

    if _comment_has_flag(comment, "@interface"):
        return INTERFACE

    if _comment_has_flag(comment, "@enum"):
        return ENUM

    if _comment_has_flag(comment, "@param") or _comment_has_flag(comment, "@return"):
        return FUNCTION

    # TODO(nnaze): Handle functions with no @param or @return.
    return PROPERTY
