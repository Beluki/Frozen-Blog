
## About

Frozen-Blog is a lightweight static blog, written in Python 3 as a [Flask][]
application. You know the gist: write posts in a markup language
(e.g. [Markdown][]), run them through a template system (e.g. [Jinja2][])
and a static, ready to deploy website comes out.

It has everything you would expect, such as pagination, post tags, syntax
highlighting and stand-alone pages. It's also a complete solution, including
both the generator and a simple, elegant theme. Both are easy to customize.

Want to see what it looks like? [click here](http://beluki.github.io/Frozen-Blog/).

Being based on [Flask][] means that you get a builtin web server with auto
reloading, an interactive debugger and easy configuration for everything.

By using [Frozen-Flask][], it's possible to generate the blog in a self-contained
fashion (relative links only). It can also clean orphan files from previous builds.
Dotfiles are ignored by default, so you can use repositories for both the source and
target folders.

Finally, because it uses [MetaFiles][], pages and posts are lazily cached and
reloaded when in live mode. This makes auto-regeneration fast, even with
thousands of posts.

## Installation and usage

To install, make sure that you are using Python 3 and install the dependencies.
You need [Frozen-Flask][], [Markdown][], [MetaFiles][], and [PyYAML][]. After
that, clone this repository and run the builtin web server:

```bash
$ blog.py -s
 * Running on http://127.0.0.1:8000/
 * Restarting with reloader
```

Edit pages and posts, tinker with templates, modify anything. All changes
will be available instantly, just refresh your web browser. When ready,
issue `blog.py -f` to actually freeze the blog to disk.

See `blog.conf` and `freezing.conf` for configuration options (you can also
change those while live, the server will restart itself). The first one is always
loaded, `freezing.conf` is only loaded when freezing.

## Portability

Frozen-Blog is tested on Windows 7 and 8 and on Debian (both x86 and x86-64)
using Python 3.3+, Flask 0.10+ and Frozen-Flask 0.11+. I always use the latest
MetaFiles from git. Python 2.x is not supported.

The encoding for pages and posts is UTF-8 with an optional BOM signature. It can
be changed in the configuration files. Input can use any newline format. The output
always uses Unix newlines (this is a Jinja2 default, it can be easily changed if needed).

The theme validates as standard HTML5 and CSS3. It looks the same on every
browser (including IE6+). It uses em-based sizes. It does not depend on Javascript
or any external CSS framework. Those are easy to add when needed.

## Status

This program is feature-complete and has no known bugs. Unless new issues
are reported or requests are made I plan no further development on it other
than maintenance.

## License

Like all my hobby projects, this is Free Software. See the [Documentation][]
folder for more information. No warranty though.

[Flask]: https://pypi.python.org/pypi/Flask
[Frozen-Flask]: https://pypi.python.org/pypi/Frozen-Flask
[Jinja2]: https://pypi.python.org/pypi/Flask
[Markdown]: https://pypi.python.org/pypi/Markdown
[MetaFiles]: https://github.com/Beluki/MetaFiles
[PyYAML]: https://pypi.python.org/pypi/PyYAML

[Documentation]: https://github.com/Beluki/Frozen-Blog/tree/master/Documentation

