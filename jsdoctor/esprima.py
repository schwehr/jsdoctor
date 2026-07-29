"""Wrappers around esprima"""

import codecs
import logging
import multiprocessing
import os
import subprocess  # nosec B404
from typing import Iterable


def GetParseInputPath() -> str:
    dir = os.path.dirname(__file__)
    return os.path.join(dir, "node/parseinput.js")


def MultiParse(sources: Iterable[str]) -> list[bytes]:
    with multiprocessing.Pool() as pool:
        results = pool.map(parse, sources)
        return results


def parse(source: str) -> bytes:
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
