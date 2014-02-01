#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frozen-Blog.
A minimal static blog written with Frozen-Flask and MetaFiles.
"""


import os
import posixpath
import sys
import time

from argparse import ArgumentParser, RawDescriptionHelpFormatter


# Information and error messages:

def outln(line):
    """ Write 'line' to stdout, using UTF-8 and platform newline. """
    print(line)


def errln(line):
    """ Write 'line' to stderr, using UTF-8 and platform newline. """
    print(line, file = sys.stderr)


# Non-builtin imports:

try:
    from flask import Flask, abort, render_template, request
    from flask_frozen import Freezer
    from MetaFiles import MetaFiles

    import markdown
    import yaml

except ImportError:
    errln('Frozen-Blog requires the following modules:')
    errln('Frozen-Flask 0.11+    - <https://pypi.python.org/pypi/Frozen-Flask>')
    errln('Markdown 2.3.1+       - <https://pypi.python.org/pypi/Markdown>')
    errln('MetaFiles 2014.01.11+ - <https://github.com/Beluki/MetaFiles>')
    errln('PyYAML 3.10+          - <https://pypi.python.org/pypi/PyYAML>')
    sys.exit(1)


# Utils:

def merge_dicts(a, b):
    """
    Merge 'a' and 'b' into a single dict.
    When the same keys are present in both dicts, 'b' has priority.
    """
    return dict(list(a.items()) + list(b.items()))


# Renderers for metadata, page and post content:

def meta_renderer(meta):
    return yaml.load(meta)

def page_renderer(body):
    return body

def post_renderer(body):
    return markdown.markdown(body, extensions = ['codehilite'])


# Sensible default configuration:

DEFAULT_CONFIGURATION = {
    'DEBUG': True,

    'PAGE_ROOT': 'page',
    'PAGE_EXTENSIONS': ('.html'),
    'PAGE_ENCODING': 'utf-8-sig',
    'PAGE_META_RENDERER': meta_renderer,
    'PAGE_BODY_RENDERER': page_renderer,

    'POST_ROOT': 'post',
    'POST_EXTENSIONS': ('.markdown'),
    'POST_ENCODING': 'utf-8-sig',
    'POST_META_RENDERER': meta_renderer,
    'POST_BODY_RENDERER': post_renderer,

    'FREEZER_DESTINATION': 'build',
    'FREEZER_DESTINATION_IGNORE': ['.*'],
    'FREEZER_RELATIVE_URLS': False,
    'FREEZER_REMOVE_EXTRA_FILES': True,

    'WWW_HOST': '127.0.0.1',
    'WWW_PORT': 8000,
}


class Target(object):
    """
    A target is a MetaFile wrapper with an additional 'path'.
    It represents a Post or a Page in the blog.
    """
    def __init__(self, metafile, path):
        self.metafile = metafile
        self.path = path

    @property
    def meta(self):
        return self.metafile.meta

    @property
    def body(self):
        return self.metafile.body


class Targets(object):
    """
    Maintains a collection of Targets that can be iterated
    and queried by path. Subclasses decide how to load content.
    """
    def __init__(self):
        self.targets = []
        self.targets_by_path = {}
        self.metafiles = None

    def __iter__(self):
        """ Iterate all the targets. """
        return iter(self.targets)

    def __getitem__(self, path):
        """ Return a given target by its path, or None when not found. """
        return self.targets_by_path.get(path)


def metafiles_as_targets(metafiles):
    """
    Iterate 'metafiles', yielding Target items with a 'path' from them.
    The 'path' is the full filepath *without extension* from the
    metafiles root, using posix separators:
    """
    for metafile in metafiles:
        fullbase, extension = os.path.splitext(metafile.filepath)
        path = os.path.relpath(fullbase, metafiles.root)
        path = path.replace(os.sep, posixpath.sep)

        yield Target(metafile, path)


class Pages(Targets):
    """ Maintains a collection of standalone Pages in the blog. """

    def initialize(self, config):
        """ Configure context options from a given 'config' dictionary. """
        self.metafiles = MetaFiles(
            root        = config['PAGE_ROOT'],
            extensions  = config['PAGE_EXTENSIONS'],
            encoding    = config['PAGE_ENCODING'],
            meta_render = config['PAGE_META_RENDERER'],
            body_render = config['PAGE_BODY_RENDERER'])

    def load(self):
        """
        Reload all the pages in the blog.
        On errors, the previous content is preserved.
        """
        pages = []
        pages_by_path = {}

        for page in metafiles_as_targets(self.metafiles):
            pages.append(page)
            pages_by_path[page.path] = page

        self.targets = pages
        self.targets_by_path = pages_by_path


class Posts(Targets):
    """ Maintains a collection of Posts in the blog. """

    def initialize(self, config):
        """ Configure context options from a given 'config' dictionary. """
        self.metafiles = MetaFiles(
            root        = config['POST_ROOT'],
            extensions  = config['POST_EXTENSIONS'],
            encoding    = config['POST_ENCODING'],
            meta_render = config['POST_META_RENDERER'],
            body_render = config['POST_BODY_RENDERER'])

    def load(self):
        """
        Reload all the posts in the blog and sort them by date.
        Posts without date are skipped (considered drafts).
        On errors, the previous content is preserved.
        """
        posts = []
        posts_by_path = {}

        for post in metafiles_as_targets(self.metafiles):
            if 'date' in post.meta:
                posts.append(post)
                posts_by_path[post.path] = post

        posts.sort(key = lambda post: post.meta['date'], reverse = True)

        self.targets = posts
        self.targets_by_path = posts_by_path


class Context(object):
    """ Maintains the collection of Pages and Posts in the blog. """

    def __init__(self):
        self.pages = Pages()
        self.posts = Posts()

    def initialize(self, config):
        """ Configure context options from a given 'config' dictionary. """
        self.pages.initialize(config)
        self.posts.initialize(config)

    def load(self):
        """ Reload all the Pages and Posts in the blog. """
        self.pages.load()
        self.posts.load()

    def get_page(self, path):
        """ Find a page by its path, or return None. """
        return self.pages[path]

    def get_post(self, path):
        """ Find a post by its path, or return None. """
        return self.posts[path]

    @property
    def environment(self):
        """
        Returns a dict containing all the data in Pages and Posts
        suitable for template rendering.
        """
        return dict(pages = self.pages, posts = self.posts)

    def render_template(self, template, **context):
        """
        Like Flask's 'render_template()' but includes our own environment.
        as well as the variables passed as parameters.
        """
        environment = merge_dicts(self.environment, context)
        return render_template(template, **environment)


# Flask application:

blog = Flask(__name__)
blog.config.update(DEFAULT_CONFIGURATION)
context = Context()


# Reloading:

@blog.before_first_request
def init_context():
    context.initialize(blog.config)
    context.load()

@blog.before_request
def auto_update_context_on_debug():
    if blog.debug:

        # avoid reloading content on static files:
        if request.endpoint == 'static':
            return

        # reload on explicit view requests (e.g. not favicons):
        if request.endpoint in blog.view_functions:
            context.load()


# Routes:

@blog.route('/')
def index():
    return context.render_template('index.html')

@blog.route('/page/<path:path>/')
def page(path):
    page = context.get_page(path) or abort(404)
    return context.render_template('page.html', page = page)

@blog.route('/post/<path:path>/')
def post(path):
    post = context.get_post(path) or abort(404)
    return context.render_template('post.html', post = post)


# Running modes:

def run_freezer():
    """ Freeze the current site state to the output folder. """
    blog.config.from_pyfile('freezing.conf', silent = True)

    if blog.debug:
        errln('Freezing in debug mode is slow.')
        errln('Set DEBUG = False in freezing.conf for a speed boost.')

    outln('Freezing...')

    start = time.clock()
    total = Freezer(blog).freeze()

    outln('Frozen: %s items.' % len(total))
    outln('Time: %s seconds.' % (time.clock() - start))


def run_server():
    """ Run the local web server and watch for changes. """
    blog.run(host = blog.config['WWW_HOST'],
             port = blog.config['WWW_PORT'],

             # also reload on configuration file changes:
             extra_files = ['blog.conf', 'freezing.conf'])


# Parser:

def make_parser():
    parser = ArgumentParser(
        description = __doc__,
        epilog = 'Example: blog.py -sf (serve, stop on control+c and freeze).',
        formatter_class = RawDescriptionHelpFormatter,
    )

    parser.add_argument('-f', '--freeze',
        help = 'freeze the current site state to the output folder',
        action = 'store_true')

    parser.add_argument('-s', '--serve',
        help = 'run the local web server and watch for changes',
        action = 'store_true')

    return parser


# Entry point:

def main():
    parser = make_parser()
    options = parser.parse_args()

    if not options.freeze and not options.serve:
        parser.print_help(sys.stderr)
        sys.exit(1)

    blog.config.from_pyfile('blog.conf', silent = True)

    if options.serve:
        run_server()

    # check if Werkzeug is running to avoid reloading code twice
    # in case the user issued both --serve and --freeze at the same time:
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        if options.freeze:
            run_freezer()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

