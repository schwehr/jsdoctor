"""Wrappers around esprima"""

import codecs
import logging
import multiprocessing
import os
import subprocess  # nosec B404
from collections.abc import Iterable


def GetParseInputPath() -> str:
    """Returns the absolute file path to the Node.js parseinput script.

    Returns:
        Path string to parseinput.js script.
    """
    dir = os.path.dirname(__file__)
    return os.path.join(dir, "node/parseinput.js")


def MultiParse(sources: Iterable[str]) -> list[bytes]:
    """Parses multiple JavaScript source strings concurrently using Node/Esprima.

    Args:
        sources: Collection of JavaScript source strings.

    Returns:
        List of parsed JSON bytes results.
    """
    with multiprocessing.Pool() as pool:
        results = pool.map(parse, sources)
        return results


def parse(source: str) -> bytes:
    """Parses a single JavaScript source string via Node/Esprima subprocess.

    Args:
        source: JavaScript source code text.

    Returns:
        Parsed AST JSON output as bytes.
    """
    with subprocess.Popen(  # nosec B603
        [GetParseInputPath()],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as proc:
        encoded_source, unused_length = codecs.getencoder("utf8")(source)
        out, err = proc.communicate(encoded_source)

        if proc.returncode != 0:
            logging.error("Error while parsing.")
            logging.error(err)
            raise Exception("Esprima parsing failed.")

        return out
