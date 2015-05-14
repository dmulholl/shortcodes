#!/usr/bin/env python3

""" Unit tests for the shortcodes module. """

import unittest
import shortcodes


@shortcodes.register('foo')
def foo(context, content, pargs, kwargs):
    return 'bar'


@shortcodes.register('wrap', 'endwrap')
def wrap(context, content, pargs, kwargs):
    return '<%s>%s</%s>' % (pargs[0], content, pargs[0])


@shortcodes.register('args')
def args(context, content, pargs, kwargs):
    for key, value in sorted(kwargs.items()):
        pargs.append(key + ':' + value)
    return '|'.join(pargs)


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
        self.assertEqual(rendered, 'bar')

    def test_simple_insertion_with_text(self):
        text = '..{% foo %}..'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '..bar..')


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
        self.assertEqual(rendered, '<div>bar</div>')

    def test_wrapping_wrapping_shortcode(self):
        text = '{% wrap div %}{% wrap p %}{% foo %}{% endwrap %}{% endwrap %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '<div><p>bar</p></div>')

    def test_wrapping_and_text_mix(self):
        text = '{% wrap div %}..{% wrap p %}.{% foo %}.{% endwrap %}..{% endwrap %}'
        rendered = shortcodes.Parser().parse(text)
        self.assertEqual(rendered, '<div>..<p>.bar.</p>..</div>')


if __name__ == '__main__':
    unittest.main()
