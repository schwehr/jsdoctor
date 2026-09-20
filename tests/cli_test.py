"""Tests for the jsdoctor.cli module."""
# pylint: disable=protected-access

import multiprocessing
import sys
import tarfile
from unittest import mock

import pytest

from jsdoctor import cli, source


def test_should_scan_path() -> None:
    """Tests that we correctly decide which files to scan."""
    assert cli._should_scan_path("foo.js") is True
    assert cli._should_scan_path("foo/bar.js") is True
    assert cli._should_scan_path("deps.js") is False
    assert cli._should_scan_path("foo/deps.js") is False
    assert cli._should_scan_path("foo_test.js") is False
    assert cli._should_scan_path("foo/bar_test.js") is False
    assert cli._should_scan_path("foo.txt") is False


def test_parse_args() -> None:
    """Tests parsing of command line arguments."""
    with mock.patch.object(
        sys,
        "argv",
        [
            "jsdoctor",
            "--tar",
            "out.tar",
            "--duplicate-symbol-is-error",
            "a.js",
            "b.js",
        ],
    ):
        args = cli._parse_args()
        assert args.tar == "out.tar"
        assert args.duplicate_symbol_is_error is True
        assert args.files == ["a.js", "b.js"]


def test_parse_args_missing_tar() -> None:
    """Tests that missing --tar causes a SystemExit."""
    with (
        mock.patch.object(sys, "argv", ["jsdoctor", "a.js"]),
        pytest.raises(SystemExit),
    ):
        cli._parse_args()


def test_scan_content() -> None:
    """Tests scanning script content into a Source object."""
    src = cli._scan_content(("a.js", "var x = 1;"))
    assert isinstance(src, source.Source)
    assert src.path == "a.js"
    # The text might be parsed differently, we just assert its a source


def test_make_content_map() -> None:
    """Tests creating a map of file paths to their content."""
    with mock.patch("builtins.open", mock.mock_open(read_data="var a = 1;")):
        content_map = cli._make_content_map(["a.js", "b.js"])
        assert content_map == {"a.js": "var a = 1;", "b.js": "var a = 1;"}


def test_make_content_map_duplicate_path() -> None:
    """Tests that duplicate paths raise an error."""
    with (
        mock.patch("builtins.open", mock.mock_open(read_data="var a = 1;")),
        pytest.raises(cli.JsDoctorError, match=r"Path already added: a\.js"),
    ):
        cli._make_content_map(["a.js", "a.js"])


def test_scan_content_in_parallel() -> None:
    """Tests parallel scanning of file content."""
    mock_pool_instance = mock.MagicMock()
    mock_pool_instance.__enter__.return_value = mock_pool_instance
    mock_pool_instance.imap.return_value = ["mock_source_1", "mock_source_2"]

    with mock.patch.object(multiprocessing, "Pool", return_value=mock_pool_instance):
        content_map = {"a.js": "var a = 1;", "b.js": "var b = 2;"}
        sources = cli._scan_content_in_parallel(content_map)

        assert sources == ["mock_source_1", "mock_source_2"]
        mock_pool_instance.imap.assert_called_once()
        # The first argument is cli._scan_content, second is dict_items
        args, _ = mock_pool_instance.imap.call_args
        assert args[0] is cli._scan_content
        # dict_items are somewhat hard to compare directly, so we convert to list
        assert list(args[1]) == [("a.js", "var a = 1;"), ("b.js", "var b = 2;")]


def test_get_symbols_from_sources() -> None:
    """Tests yielding symbols from multiple source objects."""
    src1 = mock.MagicMock(spec=source.Source)
    src1.symbols = ["symbol1", "symbol2"]

    src2 = mock.MagicMock(spec=source.Source)
    src2.symbols = ["symbol3"]

    symbols = list(cli._get_symbols_from_sources([src1, src2]))
    assert symbols == ["symbol1", "symbol2", "symbol3"]


def test_make_symbol_map() -> None:
    """Tests mapping symbols and filtering ignored identifiers."""
    sym1 = mock.MagicMock(spec=source.Symbol)
    sym1.identifier = "goog.provide"  # Should be ignored

    sym2 = mock.MagicMock(spec=source.Symbol)
    sym2.identifier = "this.foo"  # Should be ignored

    sym3 = mock.MagicMock(spec=source.Symbol)
    sym3.identifier = "my.namespace.foo"

    symbol_map = cli._make_symbol_map([sym1, sym2, sym3])

    assert len(symbol_map) == 1
    assert symbol_map["my.namespace.foo"] == sym3


def test_make_symbol_map_duplicate() -> None:
    """Tests handling duplicate symbols in _make_symbol_map."""
    sym1 = mock.MagicMock(spec=source.Symbol)
    sym1.identifier = "my.foo"

    sym2 = mock.MagicMock(spec=source.Symbol)
    sym2.identifier = "my.foo"

    # By default, duplicates log a warning and the first is kept.
    with mock.patch.object(cli._LOG, "warning") as mock_warning:
        symbol_map = cli._make_symbol_map([sym1, sym2])
        assert len(symbol_map) == 1
        assert symbol_map["my.foo"] == sym1
        mock_warning.assert_called_once()

    # If duplicate_symbol_is_error is True, it raises DuplicateSymbolError.
    with pytest.raises(cli.DuplicateSymbolError):
        cli._make_symbol_map([sym1, sym2], duplicate_symbol_is_error=True)


def test_make_namespace_map() -> None:
    """Tests mapping namespaces to sets of symbols."""
    sym1 = mock.MagicMock(spec=source.Symbol)
    sym1.namespace = "my.namespace"

    sym2 = mock.MagicMock(spec=source.Symbol)
    sym2.namespace = "my.namespace"

    sym3 = mock.MagicMock(spec=source.Symbol)
    sym3.namespace = "other.namespace"

    namespace_map = cli._make_namespace_map([sym1, sym2, sym3])

    assert len(namespace_map) == 2
    assert namespace_map["my.namespace"] == {sym1, sym2}
    assert namespace_map["other.namespace"] == {sym3}


def test_main() -> None:
    """Tests the main execution flow of the CLI."""
    mock_args = ["jsdoctor", "--tar", "out.tar", "a.js", "deps.js"]

    with (
        mock.patch.object(sys, "argv", mock_args),
        mock.patch.object(cli, "_make_content_map", return_value={"a.js": "content"}),
        mock.patch.object(cli, "_scan_content_in_parallel") as mock_scan,
        mock.patch.object(cli.generator, "GenerateHtmlDocs") as mock_gen,
        mock.patch("tarfile.open") as mock_tar_open,
    ):
        # Setup mock sources and symbols
        mock_source_obj = mock.MagicMock(spec=source.Source)
        mock_scan.return_value = [mock_source_obj]

        mock_symbol = mock.MagicMock(spec=source.Symbol)
        mock_symbol.identifier = "my.namespace.foo"
        mock_symbol.namespace = "my.namespace"
        mock_source_obj.symbols = [mock_symbol]

        # Setup generator mock to yield a dummy HTML file
        mock_gen.return_value = [("index.html", b"<html></html>")]

        # Setup tarfile mock
        mock_tar_instance = mock.MagicMock()
        mock_tar_open.return_value.__enter__.return_value = mock_tar_instance

        cli.main()

        mock_tar_open.assert_called_once_with(name="out.tar", mode="w")

        # Assert that addfile was called
        mock_tar_instance.addfile.assert_called_once()

        args, _ = mock_tar_instance.addfile.call_args
        tar_info, bytes_io = args
        assert isinstance(tar_info, tarfile.TarInfo)
        assert tar_info.name == "index.html"
        assert tar_info.size == len(b"<html></html>")

        # BytesIO content can be read to verify
        assert bytes_io.getvalue() == b"<html></html>"
