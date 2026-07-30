"""Utility functions for linking URLs and symbol references in text."""

import re
from collections.abc import Iterable

_WEB_URL_RE = re.compile(r"https?://[^\s]*")


def _replace_web_url(url_match: re.Match) -> str:
    url = url_match.group(0)
    link = f'<a href="{url}">{url}</a>'
    return link


# pylint: disable-next=invalid-name
def LinkifyWebUrls(content: str) -> str:
    """Replaces web URLs in text with HTML anchor elements.

    Args:
        content: Text containing potential URLs.

    Returns:
        Text with web URLs replaced by HTML links.
    """
    return _WEB_URL_RE.sub(_replace_web_url, content)


_SYMBOL_RE = re.compile(r"(\w+(?:\.\w+)*)(#\w+)?")


def _replace_symbol(match: re.Match[str], symbols: Iterable[str]) -> str:
    full_match = match.group(0)
    symbol_portion = match.group(1)
    # hash_portion = match.group(2)

    if symbol_portion in symbols:
        href = f"{symbol_portion}.html"

        # TODO(schwehr): This did not do anything..
        # if hash_portion:
        #   href + hash_portion

        return f'<a href="{href}">{full_match}</a>'

    return full_match


# pylint: disable-next=invalid-name
def LinkifySymbols(content: str, symbols: Iterable[str]) -> str:
    """Replaces symbol references in text with HTML links to symbol documentation.

    Args:
        content: Text containing symbol names.
        symbols: Collection of known symbol identifiers.

    Returns:
        Text with matched symbol references replaced by HTML links.
    """
    return _SYMBOL_RE.sub(lambda match: _replace_symbol(match, symbols), content)
