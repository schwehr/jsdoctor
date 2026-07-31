#!/usr/bin/env python

"""Process a JSON file tree."""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Mapping

from jsdoctor import esprima


# pylint: disable-next=invalid-name
def ProcessJsonTree(
    json_obj: Mapping[str, str],
) -> dict[str, dict[str, str | bytes]]:
    """Parses a dictionary of file paths to JavaScript sources into AST representations.

    Args:
        json_obj: Dictionary mapping file paths to JavaScript source strings.

    Returns:
        A dictionary mapping file paths to source and parsed AST dicts.
    """
    items = json_obj.items()
    paths = [pair[0] for pair in items]
    sources = [pair[1] for pair in items]

    logging.info("Parsing sources...")
    asts = esprima.MultiParse(sources)

    source_count = len(items)
    assert (
        len(paths) == source_count
        and len(sources) == source_count
        and len(asts) == source_count
    )

    results = zip(paths, sources, asts, strict=False)

    result = {}
    for path, source, ast in results:
        result[path] = {"source": source, "ast": ast}

    return result


def main() -> None:
    """Reads JSON file tree from stdin, parses sources via Esprima,

    and writes JSON to stdout.
    """
    logging.basicConfig(level=logging.INFO)
    input_data = sys.stdin.read()
    obj = json.loads(input_data)
    result = ProcessJsonTree(obj)
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
