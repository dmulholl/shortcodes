# --------------------------------------------------------------------------
# A library for parsing customizable Wordpress-style shortcodes.
#
# Author: Darren Mulholland <darren@mulholland.xyz>
# License: Public Domain
# --------------------------------------------------------------------------

import re
import sys


# Library version number.
__version__ = "2.2.1"


# Globally registered shortcode handlers indexed by tag.
globaltags = {}


# Globally registered end-tags for block-scoped shortcodes.
globalends = []


# Decorator function for globally registering shortcode handlers.
def register(tag, end_tag=None):

    def register_function(function):
        globaltags[tag] = {'func': function, 'endtag': end_tag}
        if end_tag:
            globalends.append(end_tag)
        return function

    return register_function


# Decode unicode escape sequences in a string.
def decode_escapes(s):
    return bytes(s, 'utf-8').decode('unicode_escape')


# --------------------------------------------------------------------------
# Exception classes.
# --------------------------------------------------------------------------


# Base class for all exceptions raised by the library.
class ShortcodeError(Exception):
    pass


# Exception raised if the parser detects unbalanced tags.
class NestingError(ShortcodeError):
    pass


# Exception raised if the parser encounters an unrecognised tag.
class InvalidTagError(ShortcodeError):
    pass


# Exception raised if an attempt to call a shortcode function fails.
class RenderingError(ShortcodeError):
    pass


# --------------------------------------------------------------------------
# AST Nodes.
# --------------------------------------------------------------------------


# Input text is parsed into a tree of Node instances.
class Node:

    def __init__(self):
        self.children = []

    def render(self, context):
        return ''.join(child.render(context) for child in self.children)


# A Text node represents plain text located between shortcode tokens.
class Text(Node):

    def __init__(self, text):
        self.text = text

    def render(self, context):
        return self.text


# Base class for atomic and block-scoped shortcodes. Note that string escapes
# inside quoted arguments are decoded; unquoted arguments are preserved in
# their raw state.
class Shortcode(Node):

    # Regex for parsing the shortcode's arguments.
    re_args = re.compile(r"""
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

    def __init__(self, tag, argstring, func):
        self.tag = tag
        self.func = func
        self.pargs, self.kwargs = self.parse_args(argstring)
        self.children = []

    def parse_args(self, argstring):
        pargs, kwargs = [], {}
        for match in self.re_args.finditer(argstring):
            if match.group(2) or match.group(5):
                key = match.group(1) or match.group(5)
                value = match.group(3) or match.group(4) or match.group(6)
                if match.group(3) or match.group(4):
                    value = decode_escapes(value)
                if key:
                    kwargs[key] = value
                else:
                    pargs.append(value)
            else:
                pargs.append(match.group(7))
        return pargs, kwargs


# An atomic shortcode is a shortcode with no closing tag.
class AtomicShortcode(Shortcode):

    def render(self, context):
        try:
            return str(self.func(context, None, self.pargs, self.kwargs))
        except:
            raise RenderingError('error rendering [%s] shortcode' % self.tag)


# A block-scoped shortcode is a shortcode with a closing tag.
class BlockShortcode(Shortcode):

    def render(self, context):
        content = ''.join(child.render(context) for child in self.children)
        try:
            return str(self.func(context, content, self.pargs, self.kwargs))
        except:
            raise RenderingError('error rendering [%s] shortcode' % self.tag)


# --------------------------------------------------------------------------
# Parser.
# --------------------------------------------------------------------------


# A Parser instance parses input text and renders shortcodes. A single Parser
# instance can parse an unlimited number of input strings. Note that the
# parse() method accepts an arbitrary context object which it passes on to
# each shortcode's handler function.
class Parser:

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

    def parse(self, text, context=None):

        # Local, merged copies of the global and parser tag registries.
        tags = globaltags.copy()
        tags.update(self.tags)
        ends = globalends[:] + self.ends

        # Stack of in-scope nodes and their expected end-tags.
        stack, expecting = [Node()], []

        # Process the input stream of tokens.
        for token in self._tokenize(text):
            self._parse_token(token, stack, expecting, tags, ends)

        # The stack of expected end-tags should finish empty.
        if expecting:
            raise NestingError('expecting [%s]' % expecting[-1])

        # Pop the root node and render it as a string.
        return stack.pop().render(context)

    def _tokenize(self, text):
        for token in self.regex.split(text):
            if token:
                yield token

    def _parse_token(self, token, stack, expecting, tags, ends):

        # Do we have a shortcode token?
        if token.startswith(self.start):
            content = token[self.len_start:-self.len_end].strip()
            if content:
                self._parse_sc_token(content, stack, expecting, tags, ends)

        # Do we have an escaped shortcode token?
        elif token.startswith(self.esc_start):
            stack[-1].children.append(Text(token[self.len_esc:]))

        # We must have a text token.
        else:
            stack[-1].children.append(Text(token))

    def _parse_sc_token(self, content, stack, expecting, tags, ends):

        # Split the token's content into the tag and argument string.
        tag = content.split(None, 1)[0]
        argstring = content[len(tag):]

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
                node = BlockShortcode(tag, argstring, tags[tag]['func'])
                stack[-1].children.append(node)
                stack.append(node)
                expecting.append(tags[tag]['endtag'])
            else:
                node = AtomicShortcode(tag, argstring, tags[tag]['func'])
                stack[-1].children.append(node)

        # We have an unrecognised tag.
        else:
            msg = '[%s] is not a recognised shortcode tag'
            raise InvalidTagError(msg % tag)
