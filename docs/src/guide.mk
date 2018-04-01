---
title: Guide
---

### Registering Shortcodes

You can create a new shortcode by registering a handler function for its tag using the `@register` decorator:

::: python

    import shortcodes

    @shortcodes.register("tag")
    def handler(context, content, pargs, kwargs):
        ...
        return replacement_text

Specifying a closing tag gives the new shortcode block scope:

::: python

    @shortcodes.register("tag", "endtag")
    def handler(context, content, pargs, kwargs):
        ...
        return replacement_text

A handler function should accept four arguments:

1. `context`: an arbitrary context object.
2. `content`: a string containing the shortcode's content.
3. `pargs`: a list of the shortcode's positional arguments.
4. `kwargs`: a dictionary of the shortcode's keyword arguments.

If the shortcode has block scope, `content` will be a string containing its parsed content. If the shortcode is atomic, `content` will instead have the value `None`.

Positional and keyword arguments are passed as strings. The function itself should return a string which will replace the shortcode in the parsed text.

Handlers registered using the `@register` decorator are available globally. If you need to avoid global state in your application you can register handlers on an individual parser instance instead:

::: python

    parser = shortcodes.Parser()
    parser.register(handler, tag, endtag=None)



### Processing Text

To parse an input string containing shortcodes, create a `Parser` instance and run the string through its `parse()` method:

::: python

    parser = shortcodes.Parser()
    output = parser.parse(text, context=None)

A single `Parser` instance can process an unlimited number of input strings. The `parse()` method's optional `context` argument accepts an arbitrary object to pass on to the registered handler functions.


### Customizing Shortcode Syntax

The `Parser` object's constructor accepts a number of optional arguments which you can use to customize the syntax of your shortcodes:

::: python

    parser = shortcodes.Parser(start="\[%", end="%]", esc="\\\\")

The escape sequence (a single backslash by default) allows you to escape shortcodes in your text, i.e. the escaped shortcode `\\\[% foo %]` will be rendered as the literal text `\[% foo %]`.



### Exceptions

The following exception types may be raised by the library:

*  `shortcodes.ShortcodeError`

    Base class for all shortcode exceptions.

    *   `shortcodes.NestingError`

        Raised if the parser detects unbalanced or improperly nested shortcode tags.

    *   `shortcodes.InvalidTagError`

        Raised if the parser encounters an unrecognised shortcode tag.

    *   `shortcodes.RenderingError`

        Raised if a shortcode handler throws an exception. Note that the
        `RenderingError` instance wraps the original exception which can be
        accessed via its `__cause__` attribute.



### Example

Let's make a very simple shortcode to mark a block of text as a HTML code sample. We'll use the word `code` as our tag.

Our shortcode will accept a single argument --- the name of the programming language --- and will have block scope as it needs to enclose a block of content. We'll choose the word `endcode` as our closing tag.

::: python

    import shortcodes
    import html

    @shortcodes.register("code", "endcode")
    def handler(context, content, pargs, kwargs):
        lang = pargs[0]
        code = html.escape(content)
        return '<pre class="%s">%s</pre>' % (lang, code)

We're done. Now we can try it with some input text:

    \[% code python %]
    def hello_world():
        print('hello, world')
    \[% endcode %]

If we create a `Parser` object and run the input above through its `parse()` method it will give us back the following output:

::: html

    <pre class="python">
    def hello_world():
        print('hello, world')
    </pre>
