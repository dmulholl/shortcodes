"""
A generic, customizable shortcode parser.

Parses shortcodes of the form:

    {% tag arg1 'arg 2' key1=arg3 key2='arg 4' %} [ ... {% endtag %} ]

Shortcodes can be atomic or block-scoped and can be nested to any depth.
Innermost shortcodes are processed first.
    
String escapes inside quoted arguments are decoded; unquoted arguments 
are preserved in their raw state.

License: This work has been placed in the public domain.

"""

__version__ = "1.0.0"


import re
import sys


# Stores registered shortcode functions indexed by tag.
tagmap = { 'endtags': [] }


# Decode string escape sequences.
# We do a version test here to allow for Python 2 support, but this 
# should be regarded as an experimental, untested feature.
if sys.version_info < (3, 0):
    decode = lambda s: s.decode('string_escape')
else:
    decode = lambda s: bytes(s, 'utf-8').decode('unicode_escape')


def register(tag, end_tag=None):
    """ Decorator for registering shortcode functions. """

    def register_function(function):
        tagmap[tag] = {'func': function, 'endtag': end_tag}
        if end_tag:
            tagmap['endtags'].append(end_tag)
        return function

    return register_function


class ShortcodeError(Exception):
    """ Base class for all exceptions raised by the module. """
    pass
    
    
class NestingError(ShortcodeError):
    """ Raised if the parser detects unbalanced tags. """
    pass
    

class InvalidTagError(ShortcodeError):
    """ Raised if the parser encounters an unknown tag. """
    pass
    
    
class RenderingError(ShortcodeError):
    """ Raised if an attempt to call a shortcode function fails. """
    pass


class Node:

    """ Input text is parsed into a tree of Node objects. """
    
    def __init__(self):
        self.children = []
        
    def render(self):
        return ''.join(child.render() for child in self.children)
    
    
class TextNode(Node):

    """ Plain text content. """

    def __init__(self, text):
        self.text = text

    def render(self):
        return self.text


class ShortcodeNode(Node):

    """ An atomic (non-block-scoped) shortcode. """

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
    
    def __init__(self, tag, argstring):
        self.tag = tag
        self.func = tagmap[tag]['func']
        self.pargs, self.kwargs = self.parse_args(argstring)
        
    def render(self):
        try:
            return str(self.func(*self.pargs, **self.kwargs))
        except Exception as e:
            raise RenderingError('error rendering [%s] tag' % self.tag)
        
    def parse_args(self, argstring):
        pargs, kwargs = [], {}
        for match in self.argregex.finditer(argstring):
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
        
    
class ScopedShortcodeNode(ShortcodeNode):

    """ A block-scoped shortcode. 

    The shortcode's content is passed as the first argument to the
    handler function.

    """

    def __init__(self, tag, argstring):
        ShortcodeNode.__init__(self, tag, argstring)
        self.children = []
        
    def render(self):
        content = ''.join(child.render() for child in self.children)
        try:
            return str(self.func(content, *self.pargs, **self.kwargs))
        except:
            raise RenderingError('error rendering [%s] tag' % self.tag)

    
class Parser:

    """ Parses text and renders shortcodes.

    A single Parser instance can parse mulitple input strings.

        parser = Parser()
        output = parser.parse(input)

    """

    def __init__(self, start='{%', end='%}', esc='!'):
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
        
    def tokenize(self, text):
        for token in self.regex.split(text):
            if token:
                yield token
                
    def parse(self, text):
        stack = [Node()]
        expecting = []
        for token in self.tokenize(text):
            if token.startswith(self.start):
                content = token[self.len_start:-self.len_end].strip()
                if content:
                    tag = content.split(None, 1)[0]
                    if tag in tagmap['endtags']:
                        if not expecting:
                            raise NestingError('not expecting [%s]' % tag)
                        elif tag == expecting[-1]:
                            stack.pop()
                            expecting.pop()
                        else:
                            msg = 'expecting [%s], found [%s]'
                            raise NestingError(msg % (expecting[-1], tag))
                    elif tag in tagmap:
                        if tagmap[tag]['endtag']:
                            node = ScopedShortcodeNode(tag, content[len(tag):])
                            stack[-1].children.append(node)
                            stack.append(node)
                            expecting.append(tagmap[tag]['endtag'])
                        else:
                            node = ShortcodeNode(tag, content[len(tag):])
                            stack[-1].children.append(node)
                    else:
                        msg = '[%s] is not a recognised shortcode tag'
                        raise InvalidTagError(msg % tag)
            elif token.startswith(self.esc_start):
                stack[-1].children.append(TextNode(token[self.len_esc:]))
            else:
                stack[-1].children.append(TextNode(token))
        if expecting:
            raise NestingError('expecting [%s]' % expecting[-1])
        return stack.pop().render()
