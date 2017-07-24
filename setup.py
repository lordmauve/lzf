from setuptools import setup


setup(
    name='lzf',
    description='CFFI-based Python binding for LZF stream compression',
    long_description=open('README.rst').read(),
    version='0.1',
    author='Daniel Pope',
    author_email='mauve@mauveweb.co.uk',
    url='https://github.com/lordmauve/lzf',
    py_modules=['lzf', '_lzf'],
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["lzf_build.py:ffibuilder"],
    entry_points={
        'console_scripts': [
            'lzf = lzf:cli',
        ],
    },
    install_requires=["cffi>=1.0.0"],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Topic :: System :: Archiving :: Compression',
    ]
)
