#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frozen-Blog.
A minimal static blog written with Frozen-Flask and MetaFiles.
"""


import math
import os
import posixpath
import sys
import time
import traceback

from argparse import ArgumentParser, RawDescriptionHelpFormatter


# Information and error messages:

def outln(line):
    """ Write 'line' to stdout, using the platform encoding and newline format. """
    print(line, flush = True)


def errln(line):
    """ Write 'line' to stderr, using the platform encoding and newline format. """
    print('blog.py: error:', line, file = sys.stderr, flush = True)


def warnln(line):
    """ Like errln() but for warning messages. """
    print('blog.py: warning:', line, file = sys.stderr, flush = True)


# Non-builtin imports:

try:
    from flask import Flask, abort, render_template, render_template_string, request, url_for
    from flask_frozen import Freezer, relative_url_for
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


# Default metadata renderer for pages and posts: YAML:

def default_meta_renderer(meta):
    metadata = yaml.load(meta)

    # empty metadata:
    if metadata is None:
        return {}

    # dict?
    if not isinstance(metadata, dict):
        raise ValueError('Invalid metadata, not a dict: {}'.format(metadata))

    return metadata


# Default body renderer: none for pages, markdown for posts:

def default_page_renderer(body):
    return body

def default_post_renderer(body):
    return markdown.markdown(body, extensions = ['codehilite'])


# Data representation:

class Target(object):
    """
    A Target is a MetaFile wrapper with an additional 'path' property.
    It represents a page or a post in the blog.
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

    @staticmethod
    def from_metafiles(metafiles):
        """
        Iterate 'metafiles' yielding Target instances with a 'path' from them.
        The 'path' is set to the full filepath *without extension* from the
        metafiles root, using posix separators.
        """
        for metafile in metafiles:
            fullbase, extension = os.path.splitext(metafile.filepath)
            path = os.path.relpath(fullbase, metafiles.root)
            path = path.replace(os.sep, posixpath.sep)

            yield Target(metafile, path)


class Content(object):
    """ Maintains the collection of pages and posts in the blog. """

    def __init__(self):
        self.pages = []
        self.pages_by_path = {}

        self.posts = []
        self.posts_by_path = {}
        self.posts_by_tag = {}

        self._pages_metafiles = None
        self._posts_metafiles = None

    def initialize(self, config):
        """ Configure content options from a given 'config' dictionary. """
        self._pages_metafiles = MetaFiles(
            root        = config['PAGE_ROOT'],
            extensions  = config['PAGE_EXTENSIONS'],
            encoding    = config['PAGE_ENCODING'],
            meta_render = config['PAGE_META_RENDERER'],
            body_render = config['PAGE_BODY_RENDERER'])

        self._posts_metafiles = MetaFiles(
            root        = config['POST_ROOT'],
            extensions  = config['POST_EXTENSIONS'],
            encoding    = config['POST_ENCODING'],
            meta_render = config['POST_META_RENDERER'],
            body_render = config['POST_BODY_RENDERER'])

    def load_pages(self):
        """
        Load all the pages in the blog.
        Can be called multiple times to reload.
        On errors, the previous content is preserved.
        """
        self._pages_metafiles.load()

        pages = []
        pages_by_path = {}

        for page in Target.from_metafiles(self._pages_metafiles):
            pages.append(page)
            pages_by_path[page.path] = page

        self.pages = pages
        self.pages_by_path = pages_by_path

    def load_posts(self):
        """
        Load all the posts in the blog, sorting by date and grouping by tag.
        Posts without date are skipped (considered drafts).
        Posts without tags are put in a default ['untagged'].
        Can be called multiple times to reload.
        On errors, the previous content is preserved.
        """
        self._posts_metafiles.load()

        posts = []
        posts_by_path = {}
        posts_by_tag = {}

        for post in Target.from_metafiles(self._posts_metafiles):
            if 'date' in post.meta:
                posts.append(post)
                posts_by_path[post.path] = post

        # sort first so that tags have their posts sorted too:
        posts.sort(key = lambda post: post.meta['date'], reverse = True)

        for post in posts:
            post.meta.setdefault('tags', ['untagged'])
            for tag in post.meta['tags']:
                posts_by_tag.setdefault(tag, [])
                posts_by_tag[tag].append(post)

        self.posts = posts
        self.posts_by_path = posts_by_path
        self.posts_by_tag = posts_by_tag

    def load(self):
        """ Load all the pages and posts in the blog. """
        self.load_pages()
        self.load_posts()

    @property
    def environment(self):
        """ Return the content as a dict suitable for template rendering. """
        return {
            'pages'         : self.pages,
            'pages_by_path' : self.pages_by_path,
            'posts'         : self.posts,
            'posts_by_path' : self.posts_by_path,
            'posts_by_tag'  : self.posts_by_tag
        }


# Pagination support:

class Pagination(object):
    """
    Represents the nth 'page' from 'iterable' when split in pages
    containing at least 'per_page' items.
    """
    def __init__(self, iterable, page, per_page):
        self.iterable = iterable
        self.page = page
        self.per_page = per_page

    @property
    def total_pages(self):
        """ Number of available pages. """
        return int(math.ceil(len(self.iterable) / self.per_page))

    @property
    def has_prev(self):
        """ True when there is a previous page. """
        return self.page > 1

    @property
    def has_next(self):
        """ True when there is a next page. """
        return self.page < self.total_pages

    @property
    def items(self):
        """ Get all the items from our iterable for the current page. """
        index = self.page - 1

        start = index * self.per_page
        end = start + self.per_page

        return self.iterable[start:end]


# Actual blog application:

class Blog(object):

    def __init__(self):
        self.app = Flask(__name__)
        self.app.config.update(self.default_configuration)

        self.content = Content()
        self.freezing = False

    @property
    def default_configuration(self):
        """ Sensible defaults for all our configuration options. """
        return {
            'DEBUG': True,

            'PAGE_ROOT': 'page',
            'PAGE_EXTENSIONS': '.html',
            'PAGE_ENCODING': 'utf-8-sig',
            'PAGE_META_RENDERER': default_meta_renderer,
            'PAGE_BODY_RENDERER': default_page_renderer,

            'POST_ROOT': 'post',
            'POST_EXTENSIONS': '.markdown',
            'POST_ENCODING': 'utf-8-sig',
            'POST_META_RENDERER': default_meta_renderer,
            'POST_BODY_RENDERER': default_post_renderer,

            'FREEZER_BASE_URL': 'http://localhost/',
            'FREEZER_DESTINATION': 'build',
            'FREEZER_DESTINATION_IGNORE': ['.*'],
            'FREEZER_RELATIVE_URLS': False,
            'FREEZER_REMOVE_EXTRA_FILES': True,

            'WWW_HOST': '127.0.0.1',
            'WWW_PORT': 8000,
        }

    def _install_content_handlers(self):
        """
        Install functions to initialize content on the first request
        and auto-reload it on each request, unless freezing.
        """
        @self.app.before_first_request
        def init_content():
            self.content.initialize(self.app.config)
            self.content.load()

        if self.freezing:
            return

        @self.app.before_request
        def auto_update_content():
            # avoid reloading on static files:
            if request.endpoint == 'static':
                return

            # reload on explicit view requests only (e.g. not favicons):
            if request.endpoint in self.app.view_functions:
                self.content.load()

    def _install_template_filters(self):
        """
        Install additional template filters to support pagination
        and templatize posts.
        """
        @self.app.template_filter('templatize')
        def templatize(text, environment = {}):
            return render_template_string(text, **environment)

        @self.app.template_filter('paginate')
        def paginate(iterable, page, per_page):
            return Pagination(iterable, page, per_page)

    def _install_url_for_wrappers(self):
        """
        Add convenient url_for() shortcuts.
        """

        # python code is unaffected by Frozen-Flask unless
        # it explicitly uses relative_url_for(), so check:

        if self.freezing and self.app.config['FREEZER_RELATIVE_URLS']:
            current_url_for = relative_url_for
        else:
            current_url_for = url_for

        def url_index(page = None):
            return current_url_for('index', page = page)

        def url_archive(tag = None):
            return current_url_for('archive', tag = tag)

        def url_page(page):
            return current_url_for('page', path = page.path)

        def url_page_by_path(path):
            return current_url_for('page', path = path)

        def url_post(post):
            return current_url_for('post', path = post.path)

        def url_post_by_path(path):
            return current_url_for('post', path = path)

        def url_static(filename):
            return current_url_for('static', filename = filename)

        @self.app.context_processor
        def url_for_wrappers():
            return {
                'url_index'        : url_index,
                'url_archive'      : url_archive,
                'url_page'         : url_page,
                'url_page_by_path' : url_page_by_path,
                'url_post'         : url_post,
                'url_post_by_path' : url_post_by_path,
                'url_static'       : url_static
            }

    def _install_routes(self):
        """
        Add routes for the index, archive, pages and posts.
        """
        @self.app.route('/', defaults = { 'page': 1 })
        @self.app.route('/<int:page>/')
        def index(page = 1):
            return self.render_template('index.html', page = page)

        @self.app.route('/archive/')
        @self.app.route('/archive/<tag>/')
        def archive(tag = None):
            if tag is not None and not tag in self.content.posts_by_tag:
                abort(404)
            return self.render_template('archive.html', tag = tag)

        @self.app.route('/page/<path:path>/')
        def page(path):
            current_page = self.content.pages_by_path.get(path) or abort(404)
            return self.render_template('page.html', page = current_page)

        @self.app.route('/post/<path:path>/')
        def post(path):
            current_post = self.content.posts_by_path.get(path) or abort(404)
            return self.render_template('post.html', post = current_post)

    def _install_everything(self):
        """
        Install everything needed for the blog to run.
        """
        self._install_content_handlers()
        self._install_template_filters()
        self._install_url_for_wrappers()
        self._install_routes()

    def render_template(self, template, **context):
        """
        Like Flask's 'render_template()' but includes the blog content
        as well as the variables passed as parameters.
        """
        environment = merge_dicts(self.content.environment, context)
        return render_template(template, **environment)

    def serve(self):
        """
        Run in server mode.
        """
        self.freezing = False
        self.app.config.from_pyfile('blog.conf', silent = True)
        self._install_everything()

        self.app.run(host = self.app.config['WWW_HOST'],
                     port = self.app.config['WWW_PORT'],

                     # also reload on configuration file changes:
                     extra_files = ['blog.conf'])

    def freeze(self):
        """
        Freeze the blog state to disk.
        """
        self.freezing = True
        self.app.config.from_pyfile('blog.conf', silent = True)
        self.app.config.from_pyfile('freezing.conf', silent = True)
        self._install_everything()

        try:
            outln('Freezing...')

            start = time.clock()
            total = Freezer(self.app).freeze()

            outln('Frozen: {} items.'.format(len(total)))
            outln('Time: {:.3} seconds.'.format(time.clock() - start))

        except Exception as err:
            errln('Exception while freezing: {}'.format(err))

            if not self.app.debug:
                warnln('The following traceback is not comprehensive.')
                warnln('Set DEBUG = True in freezing.conf for a more detailed traceback.')

            traceback.print_exc()
            sys.exit(1)


# Parser:

def make_parser():
    parser = ArgumentParser(
        description = __doc__,
        formatter_class = RawDescriptionHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group(required = True)

    group.add_argument('-f', '--freeze',
        help = 'freeze the current site state to the output folder',
        action = 'store_true')

    group.add_argument('-s', '--server',
        help = 'run the local web server and watch for changes',
        action = 'store_true')

    return parser


# Entry point:

def main():
    parser = make_parser()
    options = parser.parse_args()

    blog = Blog()

    if options.server:
        blog.serve()

    if options.freeze:
        blog.freeze()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

