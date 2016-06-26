#!/usr/bin/env python3
# --------------------------------------------------------------------------
# Unit tests for the shortcodes module. Run using pytest.
# --------------------------------------------------------------------------

import shortcodes


# --------------------------------------------------------------------------
# Test handlers.
# --------------------------------------------------------------------------


@shortcodes.register('foo')
def foo_handler(context, content, pargs, kwargs):
    return 'bar'


@shortcodes.register('wrap', 'endwrap')
def wrap_handler(context, content, pargs, kwargs):
    return '<%s>%s</%s>' % (pargs[0], content, pargs[0])


@shortcodes.register('args')
def args_handler(context, content, pargs, kwargs):
    for key, value in sorted(kwargs.items()):
        pargs.append(key + ':' + value)
    return '|'.join(pargs)


@shortcodes.register('context')
def context_handler(context, content, pargs, kwargs):
    return str(context)


# --------------------------------------------------------------------------
# Basic shortcode insertion tests.
# --------------------------------------------------------------------------


def test_parse_empty_string():
    text = ''
    rendered = shortcodes.Parser().parse(text)
    assert rendered == ''


def test_parse_string_no_shortcodes():
    text = 'foo'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == 'foo'


def test_parse_single_shortcode():
    text = '[% foo %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == 'bar'


def test_parse_single_shortcode_with_text():
    text = '..[% foo %]..'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == '..bar..'


# --------------------------------------------------------------------------
# Test shortcode escaping.
# --------------------------------------------------------------------------


def test_escaped_shortcode():
    text = r'\[% foo %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == '[% foo %]'


def test_double_escaped_shortcode():
    text = r'\\[% foo %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == r'\[% foo %]'


# --------------------------------------------------------------------------
# Test shortcode arguments.
# --------------------------------------------------------------------------


def test_args_with_double_quoted_strings():
    text = '[% args arg1 "arg 2" key1=arg3 key2="arg 4" %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == 'arg1|arg 2|key1:arg3|key2:arg 4'


def test_args_with_single_quoted_strings():
    text = "[% args arg1 'arg 2' key1=arg3 key2='arg 4' %]"
    rendered = shortcodes.Parser().parse(text)
    assert rendered == 'arg1|arg 2|key1:arg3|key2:arg 4'


# --------------------------------------------------------------------------
# Test shortcode nesting.
# --------------------------------------------------------------------------


def test_wrapping_simple_text():
    text = '[% wrap div %]foo[% endwrap %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == '<div>foo</div>'


def test_wrapping_shortcode():
    text = '[% wrap div %][% foo %][% endwrap %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == '<div>bar</div>'


def test_wrapping_wrapping_shortcode():
    text = '[% wrap div %][% wrap p %][% foo %][% endwrap %][% endwrap %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == '<div><p>bar</p></div>'


def test_wrapping_and_text_mix():
    text = '[% wrap div %]..[% wrap p %].[% foo %].[% endwrap %]..[% endwrap %]'
    rendered = shortcodes.Parser().parse(text)
    assert rendered == '<div>..<p>.bar.</p>..</div>'


# --------------------------------------------------------------------------
# Test context object support.
# --------------------------------------------------------------------------


def test_context_object():
    text = '[% context %]'
    rendered = shortcodes.Parser().parse(text, 101)
    assert rendered == '101'


# --------------------------------------------------------------------------
# Test local handler registration.
# --------------------------------------------------------------------------


def test_locally_registered_handler():
    text = '[% local %]'
    parser = shortcodes.Parser()
    parser.register(foo_handler, 'local')
    rendered = parser.parse(text)
    assert rendered == 'bar'


def test_locally_registered_wrap():
    text = '[% localwrap div %]foo[% endlocalwrap %]'
    parser = shortcodes.Parser()
    parser.register(wrap_handler, 'localwrap', 'endlocalwrap')
    rendered = parser.parse(text)
    assert rendered == '<div>foo</div>'
