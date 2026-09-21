#!/usr/bin/env python
"""Command-line interface for jsdoctor API documentation generator."""

import argparse
import collections
import io
import logging
import multiprocessing
import os
import pathlib
import tarfile
from collections.abc import Iterable, Iterator, Mapping

from jsdoctor import generator, source

_LOG = logging.getLogger(__name__)


def _should_scan_path(path: str) -> bool:
    _, filename = os.path.split(path)

    if not filename.endswith(".js"):
        return False

    if filename == "deps.js":
        return False

    return not filename.endswith("_test.js")


_IGNORED_IDENTIFIERS = frozenset(["goog.provide", "goog.require", "goog.setTestOnly"])


def _get_symbols_from_sources(
    sources: Iterable[source.Source],
) -> Iterator[source.Symbol]:
    for s in sources:
        yield from s.symbols


def _make_symbol_map(
    symbols: Iterable[source.Symbol],
    duplicate_symbol_is_error: bool = False,
) -> dict[str, source.Symbol]:
    symbol_map: dict[str, source.Symbol] = {}

    for symbol in symbols:
        identifier = symbol.identifier

        if identifier in _IGNORED_IDENTIFIERS:
            continue

        if identifier.startswith("this."):
            _LOG.info('Skipping "this" identifier %s', identifier)
            continue

        if identifier in symbol_map:
            duplicate_symbol = symbol_map[identifier]
            msg = f"Symbol duplicated\n{symbol}\n{duplicate_symbol}"

            if duplicate_symbol_is_error:
                raise DuplicateSymbolError(msg)

            _LOG.warning(msg)
            continue

        symbol_map[identifier] = symbol

    return symbol_map


class JsDoctorError(Exception):
    """Base exception class for jsdoctor errors."""


class DuplicateSymbolError(JsDoctorError):
    """Exception raised when a duplicate symbol identifier is encountered."""


def _make_namespace_map(
    symbols: Iterable[source.Symbol],
) -> dict[str, set[source.Symbol]]:
    namespace_map: dict[str, set[source.Symbol]] = collections.defaultdict(set)
    for symbol in symbols:
        assert symbol.namespace is not None
        namespace_map[symbol.namespace].add(symbol)
    return namespace_map


def _scan_content(content_pair: tuple[str, str]) -> source.Source:
    path, content = content_pair
    return source.ScanScript(content, path)


def _scan_content_in_parallel(
    content_map: Mapping[str, str],
) -> list[source.Source]:
    with multiprocessing.Pool(20 * multiprocessing.cpu_count()) as pool:
        return list(pool.imap(_scan_content, content_map.items()))


def _make_content_map(paths: Iterable[str]) -> dict[str, str]:
    content_map = {}
    for path in paths:
        if path in content_map:
            raise JsDoctorError(f"Path already added: {path}")

        content = pathlib.Path(path).read_text(encoding="utf-8")

        content_map[path] = content

    return content_map


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generates HTML docs for JsDoc")
    parser.add_argument("--tar", help="Path to tar file", required=True)
    parser.add_argument(
        "--duplicate-symbol-is-error",
        action="store_true",
        help="Raise an error when duplicate symbols are encountered",
    )
    parser.add_argument("files", help="Paths to files", nargs="*")
    return parser.parse_args()


def main() -> None:
    """Parses command-line arguments and generates the documentation tar archive."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(module)s:%(lineno)d: %(message)s",
    )

    result = _parse_args()
    tar_path = result.tar

    paths = result.files
    paths = [path for path in paths if _should_scan_path(path)]

    _LOG.info("Found %s paths.", len(paths))
    _LOG.info("Reading file contents.")
    content_map = _make_content_map(paths)

    sources = _scan_content_in_parallel(content_map)
    symbols = _get_symbols_from_sources(sources)

    # This could instead be just a dupe check
    symbol_map = _make_symbol_map(
        symbols,
        duplicate_symbol_is_error=result.duplicate_symbol_is_error,
    )

    symbols = symbol_map.values()

    namespace_map = _make_namespace_map(symbols)

    _LOG.info("Writing to tar: %s", tar_path)
    with tarfile.open(name=tar_path, mode="w") as tar:
        for path, content in generator.GenerateHtmlDocs(namespace_map):
            _LOG.info("Writing doc to tar: %s", path)
            # Add each path to the tar
            info = tarfile.TarInfo(name=path)
            info.size = len(content)
            buf = io.BytesIO(content)
            tar.addfile(info, buf)
    _LOG.info("Tar written to %s", tar_path)


if __name__ == "__main__":
    main()
