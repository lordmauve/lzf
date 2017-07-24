from cffi import FFI
ffibuilder = FFI()

ffibuilder.set_source("_lzf",
   r"""
        #include <lzf.h>
    """,
    libraries=['lzf'],   # or a list of libraries to link with
    include_dirs=['liblzf'],
    library_dirs=['liblzf'],
    # (more arguments like setup.py's Extension class:
    # include_dirs=[..], extra_objects=[..], and so on)
)


# Might need this define to be implemented
#define LZF_MAX_COMPRESSED_SIZE(n) ((((n) * 33) >> 5 ) + 1)

ffibuilder.cdef(r"""
#define LZF_VERSION 0x0106

unsigned int lzf_compress(
    const void *const in_data,  unsigned int in_len,
    void *out_data, unsigned int out_len);

unsigned int lzf_decompress(
    const void *const in_data, unsigned int in_len,
    void *out_data, unsigned int out_len);
""")



if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
