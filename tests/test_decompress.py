"""Tests for the lzf library."""

import os.path
from itertools import islice

import lzf


testdata = os.path.join(
    os.path.dirname(__file__),
    '..', 'testdata', 'pg19221.txt.lzf'
)


def test_iter_decompress():
    with open(testdata, 'rb') as f:
        chunks = list(islice(lzf._iter_decompress(f), 2))
    start = bytearray().join(chunks)

    assert start.startswith(
        b'The Project Gutenberg EBook of The Golden Treasury'
    )


def test_open():
    with lzf.open(testdata, 'r') as f:
        chars = f.read(20)
    assert chars == u'The Project Gutenber'


def test_open_binary():
    with lzf.open(testdata, 'rb') as f:
        chars = f.read(20)
    assert chars == b'The Project Gutenber'

