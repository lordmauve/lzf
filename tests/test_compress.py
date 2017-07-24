"""Test that we can compress data using lzf."""

import os.path
from io import BytesIO
from itertools import islice

import lzf


def test_compress():
    out = BytesIO()
    w = lzf.Writer(out)
    input = b'hello world ' * 100
    with w:
        w.write(input)

    compressed = out.getvalue()
    assert compressed.startswith(b'ZV')
    assert len(compressed) <= len(input)


def test_compress_decompress():
    out = BytesIO()
    w = lzf.Writer(out)
    with w:
        w.write(b'hello world')

    compressed = out.getvalue()
    print(repr(compressed))

    decompressed = lzf.open(BytesIO(compressed)).read()
    assert decompressed == b'hello world'
