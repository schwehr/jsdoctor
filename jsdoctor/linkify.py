import re
from typing import Iterable

_WEB_URL_RE = re.compile(r'https?://[^\s]*')


def _ReplaceWebUrl(url_match: re.Match) -> str:
  url = url_match.group(0)
  link = f'<a href="{url}">{url}</a>'
  return link


def LinkifyWebUrls(content: str) -> str:
  return _WEB_URL_RE.sub(_ReplaceWebUrl, content)

_SYMBOL_RE = re.compile(r'(\w+(?:\.\w+)*)(#\w+)?')


def _ReplaceSymbol(match: re.Match[str], symbols: Iterable[str]) -> str:
  full_match = match.group(0)
  symbol_portion = match.group(1)
  # hash_portion = match.group(2)

  if symbol_portion in symbols:
    href = '%s.html' % symbol_portion

    # TODO(schwehr): This did not do anything..
    # if hash_portion:
    #   href + hash_portion

    return f'<a href="{href}">{full_match}</a>'

  return full_match


def LinkifySymbols(content: str, symbols: Iterable[str]) -> str:
  return _SYMBOL_RE.sub(
      lambda match: _ReplaceSymbol(match, symbols),
      content)
