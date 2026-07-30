"""Tests for the jsdoctor.linkify module."""

import unittest

from jsdoctor import linkify


class LinkifyTestCase(unittest.TestCase):
    """Tests for web URL and symbol linkification utilities."""

    def test_web_reg_ex(self):
        """Tests web URL regex search."""
        match = linkify._WEB_URL_RE.search("aaa http://google.com bbb")
        self.assertIsNotNone(match)
        self.assertEqual("http://google.com", match.group(0))

    def test_linkify_web_urls(self):
        """Tests linkifying web URLs into HTML anchor tags."""
        self.assertEqual(
            'aaa <a href="http://google.com">http://google.com</a> bbb',
            linkify.LinkifyWebUrls("aaa http://google.com bbb"),
        )

    def test_match_symbols(self):
        """Tests matching symbol regex patterns in text."""
        matches = linkify._SYMBOL_RE.finditer("aaa goog.dom#cars bb.cc")
        match_strings = [match.group(0) for match in matches]

        self.assertEqual(["aaa", "goog.dom#cars", "bb.cc"], match_strings)

    def test_linkify_symbols(self):
        """Tests linkifying symbol references into documentation URLs."""
        self.assertEqual(
            'aaa <a href="goog.dom.html">goog.dom#cars</a> bb.cc',
            linkify.LinkifySymbols("aaa goog.dom#cars bb.cc", {"goog.dom"}),
        )
