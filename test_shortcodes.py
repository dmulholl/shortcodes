#!/usr/bin/env python3

""" Unit tests for the shortcodes module. """

import unittest
import shortcodes


@shortcodes.register('foo')
def foo():
    return 'foo'


@shortcodes.register('wrap', 'endwrap')
def wrap(content, tag):
    return '<%s>%s</%s>' % (tag, content, tag)


@shortcodes.register('args')
def args(*pargs, **kwargs):
    arglist = list(pargs)
    for key, value in sorted(kwargs.items()):
        arglist.append(key + ':' + value)
    return '|'.join(arglist)


class InsertionTests(unittest.TestCase):

    def test_empty_string(self):
        text = ''
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '')

    def test_string_without_shortcodes(self):
        text = 'foo'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, 'foo')

    def test_simple_insertion(self):
        text = '{% foo %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, 'foo')

    def test_simple_insertion_with_text(self):
        text = '..{% foo %}..'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '..foo..')


class EscapingTests(unittest.TestCase):

    def test_escaped_shortcode(self):
        text = r'!{% foo %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '{% foo %}')

    def test_double_escaped_shortcode(self):
        text = r'!!{% foo %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '!{% foo %}')


class ArgumentTests(unittest.TestCase):

    def test_args_with_double_quoted_strings(self):
        text = '{% args arg1 "arg 2" key1=arg3 key2="arg 4" %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, 'arg1|arg 2|key1:arg3|key2:arg 4')

    def test_args_with_single_quoted_strings(self):
        text = "{% args arg1 'arg 2' key1=arg3 key2='arg 4' %}"
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, 'arg1|arg 2|key1:arg3|key2:arg 4')


class NestingTests(unittest.TestCase):

    def test_wrapping_simple_text(self):
        text = '{% wrap div %}foo{% endwrap %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '<div>foo</div>')

    def test_wrapping_shortcode(self):
        text = '{% wrap div %}{% foo %}{% endwrap %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '<div>foo</div>')
    
    def test_wrapping_wrapping_shortcode(self):
        text = '{% wrap div %}{% wrap p %}{% foo %}{% endwrap %}{% endwrap %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '<div><p>foo</p></div>')
    
    def test_wrapping_and_text_mix(self):
        text = '{% wrap div %}..{% wrap p %}.{% foo %}.{% endwrap %}..{% endwrap %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '<div>..<p>.foo.</p>..</div>')


if __name__ == '__main__':
    unittest.main()
