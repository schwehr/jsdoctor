#!/usr/bin/env python
"""Command-line interface for jsdoctor API documentation generator."""

import argparse
import collections
import io
import logging
import multiprocessing
import os
import tarfile

from jsdoctor import generator, source


def _should_scan_path(path):
    _, filename = os.path.split(path)

    if not filename.endswith(".js"):
        return False

    if filename == "deps.js":
        return False

    return not filename.endswith("_test.js")


_IGNORED_IDENTIFIERS = frozenset(["goog.provide", "goog.require", "goog.setTestOnly"])


def _get_symbols_from_sources(sources):
    for s in sources:
        yield from s.symbols


# TODO(nanaze): Make this a flag
_DUPLICATE_SYMBOL_IS_ERROR = False


def _make_symbol_map(symbols):
    symbol_map = {}

    for symbol in symbols:
        identifier = symbol.identifier

        if identifier in _IGNORED_IDENTIFIERS:
            continue

        if identifier.startswith("this."):
            logging.info('Skipping "this" identifier %s', identifier)
            continue

        if identifier in symbol_map:
            duplicate_symbol = symbol_map[identifier]
            msg = f"Symbol duplicated\n{symbol}\n{duplicate_symbol}"

            if _DUPLICATE_SYMBOL_IS_ERROR:
                raise DuplicateSymbolError(msg)

            logging.warning(msg)
            continue

        symbol_map[identifier] = symbol

    return symbol_map


class JsDoctorError(Exception):
    """Base exception class for jsdoctor errors."""


class DuplicateSymbolError(JsDoctorError):
    """Exception raised when a duplicate symbol identifier is encountered."""


def _make_namespace_map(symbols):
    namespace_map = collections.defaultdict(set)
    for symbol in symbols:
        namespace_map[symbol.namespace].add(symbol)
    return namespace_map


def _scan_content(content_pair):
    path, content = content_pair
    return source.ScanScript(content, path)


def _scan_content_in_parallel(content_map):
    with multiprocessing.Pool(20 * multiprocessing.cpu_count()) as pool:
        return list(pool.imap(_scan_content, content_map.items()))


def _make_content_map(paths):
    content_map = {}
    for path in paths:
        if path in content_map:
            raise JsDoctorError(f"Path already added: {path}")

        with open(path) as f:
            content = f.read()

        content_map[path] = content

    return content_map


def _parse_args():
    parser = argparse.ArgumentParser(description="Generates HTML docs for JsDoc")
    parser.add_argument("--tar", help="Path to tar file", required=True)
    parser.add_argument("files", help="Paths to files", nargs="*")
    return parser.parse_args()


def main():
    """Parses command-line arguments and generates the documentation tar archive."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:%(module)s:%(lineno)d: %(message)s"
    )

    result = _parse_args()
    tar_path = result.tar

    paths = result.files
    paths = [path for path in paths if _should_scan_path(path)]

    logging.info("Found %s paths.", len(paths))
    logging.info("Reading file contents.")
    content_map = _make_content_map(paths)

    sources = _scan_content_in_parallel(content_map)
    symbols = _get_symbols_from_sources(sources)

    # This could instead be just a dupe check
    symbol_map = _make_symbol_map(symbols)

    symbols = symbol_map.values()

    namespace_map = _make_namespace_map(symbols)

    logging.info("Writing to tar: %s", tar_path)
    with tarfile.open(name=tar_path, mode="w") as tar:
        for path, content in generator.GenerateHtmlDocs(namespace_map):
            logging.info("Writing doc to tar: %s", path)
            # Add each path to the tar
            info = tarfile.TarInfo(name=path)
            info.size = len(content)
            buf = io.BytesIO(content)
            tar.addfile(info, buf)
    logging.info("Tar written to %s", tar_path)


if __name__ == "__main__":
    main()
