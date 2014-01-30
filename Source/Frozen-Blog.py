#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frozen-Blog.
A minimal, easy to customize, static blog using MetaFiles and Frozen-Flask.
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
    from flask import Flask, render_template
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


# Entry point:

def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

