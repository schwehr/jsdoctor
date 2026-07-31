"""Tests for the jsdoctor.linkify module."""

from jsdoctor import linkify


def test_web_reg_ex() -> None:
    """Tests web URL regex search."""
    # pylint: disable-next=protected-access
    match = linkify._WEB_URL_RE.search("aaa http://google.com bbb")
    assert match is not None
    assert match.group(0) == "http://google.com"


def test_linkify_web_urls() -> None:
    """Tests linkifying web URLs into HTML anchor tags."""
    assert (
        linkify.LinkifyWebUrls("aaa http://google.com bbb")
        == 'aaa <a href="http://google.com">http://google.com</a> bbb'
    )


def test_match_symbols() -> None:
    """Tests matching symbol regex patterns in text."""
    # pylint: disable-next=protected-access
    matches = linkify._SYMBOL_RE.finditer("aaa goog.dom#cars bb.cc")
    match_strings = [match.group(0) for match in matches]

    assert match_strings == ["aaa", "goog.dom#cars", "bb.cc"]


def test_linkify_symbols() -> None:
    """Tests linkifying symbol references into documentation URLs."""
    assert (
        linkify.LinkifySymbols("aaa goog.dom#cars bb.cc", {"goog.dom"})
        == 'aaa <a href="goog.dom.html">goog.dom#cars</a> bb.cc'
    )
