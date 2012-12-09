#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - cli.py

    Command line interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from gkeys.log import logger

class Main(object):
    '''Main command line interface class'''

    def __init__(self, root=None):
        """ Main class init function.

        @param root: string, root path to use
        """
        self.root = root or "/"

    def __call__(self):
        logger.debug("CLI.__call__(): self.config.keys()"
            " %s", str(self.config.keys()))
        pass

