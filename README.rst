lzf
===

.. image:: https://travis-ci.org/lordmauve/lzf.svg?branch=master
    :target: https://travis-ci.org/lordmauve/lzf


``lzf`` allows reading and writing files compressed with the LZF_ compression
format.

.. _LZF: http://oldhome.schmorp.de/marc/liblzf.html

To crib some of the features listed for ``LibLZF``:

* *Very* fast compression speeds.
* Mediocre compression ratios - you can usually expect about 40-50% compression
  for typical binary data Easy to use (just two functions, no state attached).
* Freely usable (BSD-type-license)


API
---

This package provides reading and writing LZF data as Python file like objects.

``lzf.open(file, mode='r', encoding=None, errors=None)``

    Open a LZF stream for reading or writing.

    ``file`` may be a path to an on-disk file, or a file-like object open for
    reading or writing (whatever you pass to ``mode``).

    ``mode`` must be ``r`` or ``w`` to indicate reading or writing,
    optionally with ``b`` or ``t`` to indicate binary or text-mode IO. If the
    mode is text (the default), then ``U`` is also accepted to turn on
    universal newline mode.

    ``encoding`` and ``errors`` are as for the built-in ``open()``
    function.

    Note that ``lzf.open()`` takes the Python 3 model for text IO, even on
    Python 2. Unless ``mode`` contains ``'b'``, then the returned file-like
    object will read or write Unicode strings.


Examples
--------

To open an on-disk LZF-compressed text file and print it linewise::

    import lzf

    with lzf.open('/path/to/file.txt.lzf') as f:
        for line in f:
            print(line)

To compress some binary data with LZF::

    import lzf

    with lzf.open('/path/to/file.lzf', 'wb') as f:
        f.write(b'hello world')

To read LZF compressed CBOR_ structures from a URL::

    import lzf
    import cbor2
    from urllib.request import urlopen  # Use urllib2 in Python 2

    SOME_URL = 'http://example.com/data.cbor.lzf'

    with lzf.open(urlopen(SOME_URL), 'rb') as f:
        print(cbor2.load(f))


(You'll need cbor2_ installed if you want to try this.)

.. _cbor2: https://pypi.python.org/pypi/cbor2

.. _CBOR: http://cbor.io/
