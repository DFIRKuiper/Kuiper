#! /usr/bin/env python

from distutils.core import setup

setup(name='shellbags',
    author='Willi Ballenthin',
    version='0.5',
    install_requires=[
        'python-registry',
    ],
    py_modules=[
        'BinaryParser',
        'ShellItems',
        'known_guids',
    ],
    scripts=[
        'shellbags.py',
    ],
)
