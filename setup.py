#!/usr/bin/env python3
"""
Shortcodes
==========

A library for parsing customizable WordPress-style shortcodes. Useful as a
drop-in component in text-processing applications.

Supports shortcodes with space-separated positional and keyword arguments::

    [% tag arg1 "arg 2" key1=arg3 key2="arg 4" %]

Shortcodes can be atomic or block-scoped and can be nested to any depth.
Innermost shortcodes are processed first::

    [% tag %] ... content with [% more %] shortcodes ... [% endtag %]

Shortcode syntax is customizable::

    <tag arg="foo"> ... </tag>

See the project's `Github homepage <https://github.com/dmulholland/shortcodes>`_
for further details.

Note that this package requires Python 3.

"""

import os
import re
import io

from setuptools import setup


filepath = os.path.join(os.path.dirname(__file__), 'shortcodes.py')
with io.open(filepath, encoding='utf-8') as metafile:
    regex = r'''^__([a-z]+)__ = ["'](.*)["']'''
    meta = dict(re.findall(regex, metafile.read(), flags=re.MULTILINE))


setup(
    name = 'shortcodes',
    version = meta['version'],
    py_modules = ['shortcodes'],
    author = 'Darren Mulholland',
    url = 'http://mulholland.xyz/dev/shortcodes/',
    license = 'Public Domain',
    description = (
        'A generic, customizable shortcode parser.'
    ),
    long_description = __doc__,
    classifiers = [
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: OS Independent',
        'License :: Public Domain',
        'Intended Audience :: Developers',
        'Topic :: Text Processing :: General',
    ],
)
