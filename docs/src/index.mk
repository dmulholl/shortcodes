---
title: Home
meta title: Shortcodes &mdash; a Python library for parsing shortcodes
meta description: >
    This Python library supports customizable WordPress-style shortcodes with
    space-separated positional and keyword arguments.
---

This Python library supports customizable WordPress-style shortcodes with space-separated positional and keyword arguments:

    \[% tag arg1 key=arg2 %]

Arguments containing spaces can be enclosed in quotes:

    \[% tag "arg 1" key="arg 2" %]

Shortcodes can be atomic, as above, or can enclose a block of content between opening and closing tags:

    \[% tag %] ... \[% endtag %]

Block-scoped shortcodes can be nested to any depth. Innermost shortcodes are processed first:

    \[% tag %] ... content with \[% more %] shortcodes ... \[% endtag %]

Shortcode syntax is customizable:

    <tag arg="foo"> ... </tag>



### Installation

Install from the Python package index using `pip`:

    $ pip install shortcodes

Alternatively, you can incorporate the `shortcodes.py` file directly into your application. The library is entirely self-contained and its code has been placed in the public domain. You can find the code on Github [here][github].

Note that this library requires Python 3.

[github]: https://github.com/dmulholland/shortcodes



### Links

* [Github Homepage](https://github.com/dmulholland/shortcodes)
* [Python Package Index](https://pypi.python.org/pypi/shortcodes/)
* [Online Documentation](http://mulholland.xyz/docs/shortcodes/)



### License

This work has been placed in the public domain.
