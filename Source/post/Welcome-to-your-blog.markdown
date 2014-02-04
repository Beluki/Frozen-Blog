title: Welcome to your blog
date: 2014-02-04
tags: ['blogging', 'meta']

Welcome!

This is a dummy post. It's included just so that you can see what everything looks like
when there is content in the blog. Feel free to edit or delete it.

Here is some syntax-highlighted code (from Frozen-Blog itself). The width of the site
should allow for a line-length of 80 characters.

    ::python
    @blog.before_request
    def auto_update_context_on_debug():
        if blog.debug:

            # avoid reloading content on static files:
            if request.endpoint == 'static':
                return

            # reload on explicit view requests (e.g. not favicons):
            if request.endpoint in blog.view_functions:
                context.load()


By the way, this site should validate both as [HTML5][] and [CSS3][].

[HTML5]: http://validator.w3.org/check?uri=referer
[CSS3]: http://jigsaw.w3.org/css-validator/check/referer?profile=css3

