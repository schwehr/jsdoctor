#!/usr/bin/env python

"""Scans a directory tree for .js files and builds a JSON representation.

Scans a directory tree for .js files, and puts the contents into a single JSON
object map of path to content.

Output is written to stdout.

Usage:

$ genjsonfiletree.py

Scans the current directory.

$ genjsonfiletree.py path/to/dir

Scans the given directory.
"""

import json
import logging
import os
import sys
from collections.abc import Iterator


def _yield_paths(root: str) -> Iterator[tuple[str, str]]:
    for dir_root, _, files in os.walk(root):
        for file_path in files:
            abspath = os.path.join(dir_root, file_path)
            relpath = os.path.relpath(abspath, root)

            yield relpath, abspath


def _yield_js_paths(root: str) -> Iterator[tuple[str, str]]:
    for relpath, abspath in _yield_paths(root):
        _, ext = os.path.splitext(abspath)
        if ext == ".js":
            yield relpath, abspath


# pylint: disable-next=invalid-name
def ScanTree(tree_root: str) -> dict[str, str]:
    """Scans a directory tree for .js files.

    Returns a map of relative paths to content.

    Args:
        tree_root: Directory path to scan.

    Returns:
        A dictionary mapping relative file paths to their string contents.
    """
    tree: dict[str, str] = {}

    for relpath, abspath in _yield_js_paths(tree_root):
        logging.info("Reading file: %s", relpath)
        with open(abspath, encoding="utf-8") as f:
            tree[relpath] = f.read()

    return tree


def main() -> None:
    """Main entry point for scanning directory trees and writing JSON to stdout."""
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) == 1:
        logging.info("Path not specified. Using current directory as path.")
        dir_root = os.getcwd()

    elif len(sys.argv) == 2:
        dir_root = sys.argv[1]

    else:
        sys.exit(__doc__)

    logging.info('Scanning tree. Path: "%s"', dir_root)

    tree = ScanTree(dir_root)
    resulting_json = json.dumps(tree)
    sys.stdout.write(resulting_json)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
