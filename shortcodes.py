"""
A generic, customizable shortcode parser.

Parses shortcodes of the form:

    [% tag arg1 'arg 2' key1=arg3 key2='arg 4' %] ... [% endtag %]

Shortcodes can be atomic or block-scoped and can be nested to any depth.
Innermost shortcodes are processed first.

String escapes inside quoted arguments are decoded; unquoted arguments
are preserved in their raw state.

Handler functions can be registered globally using the @register decorator
or locally on an individual parser instance using its register() method:

    @shortcodes.register('tag')
    def handler(context=None, content=None, pargs=[], kwargs={}):
        ...

Specifying an end-tag creates a shortcode with block scope:

    @shortcodes.register('tag', 'endtag')
    def handler(context=None, content=None, pargs=[], kwargs={}):
        ...

Handler functions should accept four arguments:

    `context`: an arbitrary context object
    `content`: the shortcode's content as a string in the case of block-scoped
               shortcodes, or None in the case of atomic shortcodes
    `pargs`:   a list of the shortcode's positional arguments
    `kwargs`:  a dictionary of the shortcode's keyword arguments

Positional and keyword arguments are passed as strings. The handler function
itself should return a string.

To parse an input string containing shortcodes, create a Parser() object and
call its parse() method:

    parser = shortcodes.Parser()
    output = parser.parse(text, context=None)

A single Parser() object can process multiple input strings. The optional
`context` argument accepts an arbitrary object to pass on to the registered
handler functions.

Author: Darren Mulholland <darren@mulholland.xyz>
License: Public Domain

"""

import re
import sys


# Library version number.
__version__ = "2.1.0"


# Globally registered shortcode functions indexed by tag.
globaltags = {}


# Globally registered end-tags for block-scoped shortcodes.
globalends = []


def register(tag, end_tag=None):
    """ Decorator for globally registering shortcode functions. """

    def register_function(function):
        globaltags[tag] = {'func': function, 'endtag': end_tag}
        if end_tag:
            globalends.append(end_tag)
        return function

    return register_function


def decode(s):
    """ Decode string escape sequences. """
    return bytes(s, 'utf-8').decode('unicode_escape')


class ShortcodeError(Exception):
    """ Base class for all exceptions raised by the library. """
    pass


class NestingError(ShortcodeError):
    """ Raised if the parser detects unbalanced tags. """
    pass


class InvalidTagError(ShortcodeError):
    """ Raised if the parser encounters an unrecognised tag. """
    pass


class RenderingError(ShortcodeError):
    """ Raised if an attempt to call a shortcode function fails. """
    pass


class Node:

    """ Input text is parsed into a tree of Node objects. """

    def __init__(self):
        self.children = []

    def render(self, context):
        return ''.join(child.render(context) for child in self.children)


class Text(Node):

    """ Plain text. """

    def __init__(self, text):
        self.text = text

    def render(self, context):
        return self.text


class Shortcode(Node):

    """ Atomic shortcode (a shortcode with no closing tag). """

    argregex = re.compile(r"""
        (?:([^\s'"=]+)=)?
        (
            "((?:[^\\"]|\\.)*)"
            |
            '((?:[^\\']|\\.)*)'
        )
        |
        ([^\s'"=]+)=(\S+)
        |
        (\S+)
    """, re.VERBOSE)

    def __init__(self, tag, args, func):
        self.tag = tag
        self.func = func
        self.pargs, self.kwargs = self.parse_args(args)

    def render(self, context):
        try:
            return str(self.func(
                context,
                None,
                self.pargs,
                self.kwargs
            ))
        except:
            raise RenderingError('error rendering [%s] shortcode' % self.tag)

    def parse_args(self, args):
        pargs, kwargs = [], {}
        for match in self.argregex.finditer(args):
            if match.group(2) or match.group(5):
                key = match.group(1) or match.group(5)
                value = match.group(3) or match.group(4) or match.group(6)
                if match.group(3) or match.group(4):
                    value = decode(value)
                if key:
                    kwargs[key] = value
                else:
                    pargs.append(value)
            else:
                pargs.append(match.group(7))
        return pargs, kwargs


class ScopedShortcode(Shortcode):

    """ Block-scoped shortcode (a shortcode with opening and closing tags). """

    def __init__(self, tag, args, func):
        self.tag = tag
        self.func = func
        self.pargs, self.kwargs = self.parse_args(args)
        self.children = []

    def render(self, context):
        try:
            return str(self.func(
                context,
                ''.join(child.render(context) for child in self.children),
                self.pargs,
                self.kwargs
            ))
        except:
            raise RenderingError('error rendering [%s] shortcode' % self.tag)


class Parser:

    """ Parses text and renders shortcodes.

    A single Parser instance can parse multiple input strings.

        parser = Parser()
        output = parser.parse(text, context)

    The parse() method accepts an arbitrary context object which it
    passes on to the shortcode handler functions.

    """

    def __init__(self, start='[%', end='%]', esc='\\'):
        self.start = start
        self.esc_start = esc + start
        self.len_start = len(start)
        self.len_end = len(end)
        self.len_esc = len(esc)
        self.regex = re.compile(r'((?:%s)?%s.*?%s)' % (
            re.escape(esc),
            re.escape(start),
            re.escape(end),
        ))
        self.tags = {}
        self.ends = []

    def register(self, func, tag, end_tag=None):
        self.tags[tag] = {'func': func, 'endtag': end_tag}
        if end_tag:
            self.ends.append(end_tag)

    def tokenize(self, text):
        for token in self.regex.split(text):
            if token:
                yield token

    def parse(self, text, context=None):

        # Local, merged copies of the global and parser tag registries.
        tags = globaltags.copy()
        tags.update(self.tags)
        ends = globalends[:] + self.ends

        # Stack of in-scope nodes and their expected end-tags.
        stack, expecting = [Node()], []

        # Process the input stream of tokens.
        for token in self.tokenize(text):
            self.parse_token(token, stack, expecting, tags, ends)

        # The stack of expected end-tags should finish empty.
        if expecting:
            raise NestingError('expecting [%s]' % expecting[-1])

        # Pop the root node and render it as a string.
        return stack.pop().render(context)

    def parse_token(self, token, stack, expecting, tags, ends):

        # Do we have a shortcode token?
        if token.startswith(self.start):
            content = token[self.len_start:-self.len_end].strip()
            if content:
                self.parse_shortcode(content, stack, expecting, tags, ends)

        # Do we have an escaped shortcode token?
        elif token.startswith(self.esc_start):
            stack[-1].children.append(Text(token[self.len_esc:]))

        # We must have a text token.
        else:
            stack[-1].children.append(Text(token))

    def parse_shortcode(self, content, stack, expecting, tags, ends):

        # Split the content into the tag and argument string.
        tag = content.split(None, 1)[0]
        args = content[len(tag):]

        # Do we have a registered end-tag?
        if tag in ends:
            if not expecting:
                raise NestingError('not expecting [%s]' % tag)
            elif tag == expecting[-1]:
                stack.pop()
                expecting.pop()
            else:
                msg = 'expecting [%s], found [%s]'
                raise NestingError(msg % (expecting[-1], tag))

        # Do we have a registered tag?
        elif tag in tags:
            if tags[tag]['endtag']:
                node = ScopedShortcode(tag, args, tags[tag]['func'])
                stack[-1].children.append(node)
                stack.append(node)
                expecting.append(tags[tag]['endtag'])
            else:
                node = Shortcode(tag, args, tags[tag]['func'])
                stack[-1].children.append(node)

        # We have an unrecognised tag.
        else:
            msg = '[%s] is not a recognised shortcode tag'
            raise InvalidTagError(msg % tag)
