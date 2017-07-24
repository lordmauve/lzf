"""Tests for interoperability with the C lzf."""
import sys
import os
import tempfile
import subprocess
import shutil
from hashlib import sha1

import pytest

import lzf


def digest(file):
    """Return the hex SHA1 digest of an open binary file-like object."""
    h = sha1()
    with file:
        for chunk in iter(lambda: file.read(10240), b''):
            h.update(chunk)
    return h.hexdigest()


# Path to the root of the codebase
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Paths to the test data fixtures
TESTDATA = os.path.join(ROOT, 'testdata', 'time-machine.txt')
TESTDATA_SHA1 = digest(open(TESTDATA, 'rb'))

# The original lzf binary
LIBLZF_BIN = os.path.join(ROOT, 'liblzf', 'lzf')


@pytest.fixture
def testdata():
    """Test fixture to create a temporary directory containing the testdata."""
    tmpdir = tempfile.mkdtemp()
    dest = os.path.join(tmpdir, os.path.basename(TESTDATA))
    shutil.copy2(TESTDATA, dest)
    yield dest
    shutil.rmtree(tmpdir)


def test_lzf_to_py(testdata):
    """The Python lzf library can open a file compressed with liblzf."""
    subprocess.check_call([LIBLZF_BIN, '-c', testdata])
    assert digest(lzf.open(testdata + '.lzf', 'rb')) == TESTDATA_SHA1


def test_py_to_lzf(testdata):
    """liblzf can decompress a file written with the Python lzf library."""
    subprocess.check_call([sys.executable, '-m', 'lzf', '-c', testdata])
    os.unlink(testdata)
    subprocess.check_call([LIBLZF_BIN, '-d', testdata + '.lzf'])

    assert digest(open(testdata, 'rb')) == TESTDATA_SHA1


def test_py_to_py(testdata):
    """We can open a file we compressed."""
    subprocess.check_call([sys.executable, '-m', 'lzf', '-c', testdata])
    assert digest(lzf.open(testdata + '.lzf', 'rb')) == TESTDATA_SHA1
