
# Shortcodes

A Python library for parsing customizable WordPress-style shortcodes. Useful as a drop-in component in text processing applications.

Supports shortcodes with space-separated positional and keyword arguments:

    [% tag arg1 "arg 2" key=arg3 key="arg 4" %]

Shortcodes can be atomic or block-scoped and can be nested to any depth. Innermost shortcodes are processed first:

    [% tag %] ... content with [% more %] shortcodes ... [% endtag %]

Shortcode syntax is customizable:

    <tag arg="foo"> ... </tag>



## Installation

You can incorporate the `shortcodes.py` file directly into your Python application. The library is entirely self-contained and its code has been placed in the public domain.

Alternatively, you can install the shortcodes library from the Python package index using `pip`:

    $ pip install shortcodes

Note that this library requires Python 3.



## Usage

### Registering Shortcodes

Every shortcode tag has an associated handler function. You can create a new shortcode by registering its handler using the `@register` decorator:

    import shortcodes

    @shortcodes.register('tag')
    def handler(context=None, content=None, pargs=[], kwargs={}):
        ...

If you specify a closing tag the new shortcode will have block scope:

    @shortcodes.register('tag', 'endtag')
    def handler(context=None, content=None, pargs=[], kwargs={}):
        ...

A handler function should accept four arguments:

* `context`: an arbitrary context object

* `content`: the shortcode's content as a string in the case of block-scoped shortcodes, or `None` in the case of atomic shortcodes

* `pargs`: a list of the shortcode's positional arguments

* `kwargs`: a dictionary of the shortcode's keyword arguments

Positional and keyword arguments are passed as strings. The handler function
itself should return a string.

Handlers registered using the `@register` decorator are available globally. If you need to avoid global state in your application you can register handlers on an individual parser instance instead:

    parser = shortcodes.Parser()
    parser.register(handler, 'tag', 'endtag')


### Processing Text

To parse an input string containing shortcodes, create a `Parser` instance and run the string through its `parse()` method:

    parser = shortcodes.Parser()
    output = parser.parse(text, context=None)

A single `Parser` instance can process multiple input strings. The optional `context` argument accepts an arbitrary object to pass on to the registered handler functions.



### Customizing Shortcode Syntax

The `Parser` object's constructor accepts a number of optional arguments which you can use to customize the syntax of your shortcodes:

    parser = shortcodes.Parser(start='[%', end='%]', esc='\\')

The escape sequence - by default, a single backslash - allows you to escape shortcodes in your text, i.e. the escaped shortcode `\[% foo %]` will be rendered as the literal text `[% foo %]`.



### Exceptions

The following exception types may be raised by the module:

*   `shortcodes.ShortcodeError`

    Base class for all shortcode exceptions.

    *   `shortcodes.NestingError`

        Raised if the parser detects unbalanced or improperly nested shortcode tags.

    *   `shortcodes.InvalidTagError`

        Raised if the parser encounters an unrecognised shortcode tag.

    *   `shortcodes.RenderingError`

        Raised if a shortcode handler throws an exception.



## Example

Let's make a very simple shortcode to mark a block of text as a HTML code sample. We'll use the word `code` as our tag.

Our shortcode will accept a single argument - the name of the programming language - and will have block scope as it needs to enclose a block of content. We'll choose the word `endcode` as our closing tag.

    import shortcodes

    @shortcodes.register('code', 'endcode')
    def code_handler(context, content, pargs, kwargs):
        return '<pre class="%s">%s</pre>' % (pargs[0], content)

We're done. Now we can try it with some input text:

    [% code python %]
    def hello_world():
        print('hello, world')
    [% endcode %]

If we create a `Parser` object and run the input above through its `parse()` method it will give us back the following output:

    <pre class="python">
    def hello_world():
        print('hello, world')
    </pre>



## License

This work has been placed in the public domain.
