
Shortcodes
==========

A customizable shortcode parser in Python. Useful as a drop-in component in a text processing application.

Supports shortcodes with space-separated positional and keyword arguments:

    {% tag arg1 "arg 2" key1=arg3 key2="arg 4" %}

Shortcodes can have block scope and can be nested to any depth. Innermost shortcodes are processed first:

    {% tag %}
        Content can contain {% more %} shortcodes.
    {% endtag %}

Shortcode syntax is customizable:

    [tag arg="foo"] ... [/tag]


Usage
-----

### Registering Shortcodes ###

Every shortcode tag is associated with a handler function. To create a new shortcode simply register its handler function using the `@register` decorator:

    @shortcodes.register('tag')

Specifying a closing tag will give the new shortcode block scope:

    @shortcodes.register('tag', 'endtag')

Shortcode functions can accept any number of arguments. All arguments are passed as strings and the function itself should return a string. Shortcodes with block scope receive their content as their first argument.


### Processing Text ###

To process the shortcodes in a string create a `Parser` object and call its `.parse()` method:

    parser = shortcodes.Parser()
    output = parser.parse(text)

You can process multiple strings with a single `Parser` object. The constructor takes a number of optional arguments allowing you to customize the syntax of your shortcodes:

    Parser(start='{%', end='%}', esc='!')

The escape sequence - a single `!` by default - allows you to escape shortcodes in your text, i.e. the escaped shortcode `!{% foo %}` will be rendered as the literal text `{% foo %}`.


### Exceptions ###

The following exception types may be raised by the module:

*   `shortcodes.ShortcodeError`

    Base class for all shortcode exceptions.

    *   `shortcodes.NestingError`

        Raised if the parser detects unbalanced or improperly nested shortcode tags.

    *   `shortcodes.InvalidTagError`

        Raised if the parser encounters an unrecognised shortcode tag.

    *   `shortcodes.RenderingError`

        Raised if a shortcode handler throws an exception.


Example
-------

Let's make a simple shortcode to mark a block of text as an HTML code sample. We'll use the word `code` as our tag.

Our shortcode will accept a single argument - the name of the programming language - and will have block scope as it needs to enclose a block of content. We'll choose the word `endcode` as our closing tag.

    import shortcodes

    @shortcodes.register('code', 'endcode')
    def mark_as_code(content, lang):
        return '<pre class="%s">%s</pre>' % (lang, content)

We're done. Now we can try it with some sample text:

    {% code python %}
    def hello_world():
        print('hello, world')
    {% endcode %}

Creating a `Parser` object and running the input through its `.parse()` method gives us back the following string:

    <pre class="python">
    def hello_world():
        print('hello, world')
    </pre>


Requirements
------------

Requires Python 3.


License
-------

This work has been placed in the public domain.
