from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
  from . import source

CONSTRUCTOR = 'constructor'
INTERFACE = 'interface'
ENUM = 'enum'
FUNCTION = 'function'
PROPERTY = 'property'


def _CommentHasFlag(comment: source.Comment, flag_name: str) -> bool:
  assert flag_name.startswith('@'), 'flag name should start with @'
  for flag in comment.flags:
    if flag.name == flag_name:
      return True
  return False


def DetermineSymbolType(symbol: source.Symbol) -> str:
  comment = symbol.comment
  assert comment, 'Expected to have comment'

  if _CommentHasFlag(comment, '@constructor'):
    return CONSTRUCTOR

  if _CommentHasFlag(comment, '@interface'):
    return INTERFACE

  if _CommentHasFlag(comment, '@enum'):
    return ENUM

  if _CommentHasFlag(comment, '@param') or _CommentHasFlag(comment, '@return'):
    return FUNCTION

  # TODO(nnaze): Handle functions with no @param or @return.
  return PROPERTY
