import os
import struct
import io

from _lzf import lib, ffi

try:
    unicode
except NameError:
    unicode = str


HDR_U = struct.Struct('>H')
HDR_C = struct.Struct('>HH')

# Allocate the same size buffer as in LZF code; this is the max
MAX_CHUNK = 64 * 1024 - 1


def _iter_decompress(fileobj):
    """Decompress from the given fileobj, which must be binary data.

    Returns an iterable of bytearray objects.

    """
    def read(sz):
        bs = fileobj.read(sz)
        if len(bs) < sz:
            raise ValueError('Unexpected end of stream')
        return bs

    out = ffi.new('char[]', MAX_CHUNK + 16)
    try:
        fileobj.tell()
    except:
        def tell():
            return 'unknown'
    else:
        tell = fileobj.tell

    while True:
        pos = tell()
        hdr = fileobj.read(3)
        if hdr == b'ZV\0':
            us, = HDR_U.unpack(read(HDR_U.size))
            yield fileobj.read(us)
        elif hdr == b'ZV\1':
            cs, us = HDR_C.unpack(read(HDR_C.size))
            inbuf = fileobj.read(cs)
            res = lib.lzf_decompress(
                inbuf, cs,
                out, len(out)
            )
            if res == 0 or res != us:
                raise ValueError(
                    'Error decompressing LZF chunk at offset %s' % pos
                )
            # FIXME: don't unpack to bytes here, as this allocates an object
            # which isn't needed if we use readinto() - as, it seems, the
            # BufferedReader objects do.
            #
            # We can get around this by refactoring to keep writing into the
            # same buffer, and tracking how much of the buffer has been used.
            # This would require merging this generator into RawReader.
            yield ffi.unpack(out, us)
        elif hdr == b'ZV\2':
            # CRC32, skip for now
            continue
        elif not hdr or hdr == b'\0':
            return
        else:
            raise ValueError(
                'Invalid chunk header %r at offset %s' % (hdr, pos)
            )


def LZF_MAX_COMPRESSED_SIZE(n):
    return (((n * 33) >> 5) + 1)


class RawReader(io.RawIOBase):
    def __init__(self, fileobj):
        self._stream = iter(_iter_decompress(fileobj))
        self._chunk = None
        self.pos = 0

    def _next(self):
        while True:
            try:
                chunk = next(self._stream)
            except StopIteration:
                return b''
            else:
                if chunk:
                    return chunk

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return False

    def read(self, size=-1):
        if not self._chunk:
            self._chunk = self._next()
        if size == -1:
            chunk = self._chunk
            self._chunk = None
            return chunk
        else:
            chunk, self._chunk = self._chunk[:size], self._chunk[size:]
            return chunk

    def readinto(self, buf):
        b = self.read(len(buf))
        buf[:len(b)] = b
        return len(b)


class Reader(io.BufferedReader):
    def __init__(self, fileobj):
        super(Reader, self).__init__(RawReader(fileobj))


class Writer(io.RawIOBase):
    def __init__(self, outfile):
        self._outfile = outfile
        self._buf = bytearray()
        self._dest = bytearray(LZF_MAX_COMPRESSED_SIZE(MAX_CHUNK))
        self._hdr_c = bytearray(HDR_C.size + 3)
        self._hdr_c[:3] = b'ZV\1'
        self._hdr_u = bytearray(HDR_U.size + 3)
        self._hdr_u[:3] = b'ZV\0'

    def readable(self):
        return False

    def writable(self):
        return True

    def seekable(self):
        return False

    def write(self, bs):
        self._buf.extend(bs)
        if len(self._buf) >= MAX_CHUNK:
            self._flush_chunk()

    def flush(self):
        while self._buf:
            self._flush_chunk()
        self._outfile.flush()

    def _flush_chunk(self):
        us = min(len(self._buf), MAX_CHUNK)
        cs = lib.lzf_compress(
            ffi.from_buffer(self._buf), us,
            ffi.from_buffer(self._dest), MAX_CHUNK
        )
        if cs > us:
            HDR_U.pack_into(self._hdr_u, 3, us)
            self._outfile.write(self._hdr_u)
            self._outfile.write(memoryview(self._buf)[:us])
        else:
            HDR_C.pack_into(self._hdr_c, 3, cs, us)
            self._outfile.write(self._hdr_c)
            self._outfile.write(memoryview(self._dest)[:cs])
        del self._buf[:us]

    def close(self):
        self.flush()



file_open = open


def open(file, mode='r', encoding=None, errors=None):
    """Open a LZF stream for reading or writing.

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

    """
    op = mode[0]
    modeflags = set(mode[1:])
    valid_mode = (
        mode and
        op in {'r', 'w'} and
        modeflags.issubset('Ubt') and
        not ('b' in mode and modeflags.intersection('tU'))
    )
    if not valid_mode:
        raise ValueError('Unsupported mode %r' % mode)

    if isinstance(file, (str, unicode)):
        file = file_open(file, op + 'b')

    if op == 'r':
        lzfio = Reader(file)
    else:
        lzfio = Writer(file)

    if 'b' not in mode:
        newline = None if mode == 'rU' else os.linesep
        lzfio = io.TextIOWrapper(
            lzfio,
            encoding=encoding,
            errors=errors,
            newline=newline
        )
    return lzfio


lzf_open = open


def copy_from(inf, outf):
    """Copy the contents of inf to outf."""
    while True:
        chunk = inf.read(64 * 1024)
        if not chunk:
            break
        outf.write(chunk)


def cli():
    """Run as a command-line compression tool."""
    from argparse import ArgumentParser

    parser = ArgumentParser()

    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        '-d',
        '--decompress',
        action='store_true',
        help="Decompress the input file."
    )
    action.add_argument(
        '-c',
        '--compress',
        action='store_true',
        help="Compress the input file."
    )

    parser.add_argument(
        'filename',
        help="The file to operator on."
    )

    opts = parser.parse_args()

    if opts.compress:
        in_file = opts.filename
        out_file = in_file + '.lzf'
        with file_open(in_file, 'rb') as inf, lzf_open(out_file, 'wb') as outf:
            copy_from(inf, outf)
    else:
        in_file = opts.filename
        if not in_file.endswith('.lzf'):
            parser.error("Compressed filename must end with '.lzf'")
        out_file = in_file[:-4]
        if not os.path.basename(out_file):
            parser.error("Invalid filename '%r'" % out_file)

        with lzf_open(in_file, 'rb') as inf, file_open(out_file, 'wb') as outf:
            copy_from(inf, outf)


if __name__ == '__main__':
    cli()
