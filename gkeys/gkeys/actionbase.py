#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - actionbase.py

    Base api interface module

    @copyright: 2012-2015 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function

import os
import sys

if sys.version_info[0] >= 3:
    _unicode = str
else:
    _unicode = unicode


from snakeoil.demandload import demandload

demandload(
    "json:load",
    "gkeys.lib:GkeysGPG",
    "gkeys.keyhandler:KeyHandler",
)



class ActionBase(object):
    '''Base actions class holding comon functions and init'''

    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger
        self.seeds = None
        self._seedhandler = None
        self._keyhandler = None
        self._gpg = None
        self.category = None


    @property
    def gpg(self):
        '''Holds the classwide GkeysGPG instance'''
        if not self._gpg:
            self._gpg = GkeysGPG(self.config,
                self._set_category(self.category), self.logger)
        else:
            self._gpg.basedir = self._set_category(self.category)
        return self._gpg


    @property
    def keyhandler(self):
        '''Holds the classwide KeyHandler instance'''
        if not self._keyhandler:
            self._init_keyhandler()
        return self._keyhandler


    def _init_keyhandler(self):
        self._keyhandler = KeyHandler(self.config, self.logger)
        self._seedhandler = self._keyhandler.seedhandler


    @property
    def seedhandler(self):
        '''Holds the classwide SeedHandler instance
        which is a convienience variable for the keyhandler's instance of it'''
        if not self._seedhandler:
            self._init_keyhandler()
        return self._seedhandler


    def _set_category(self, cat):
        keyring = self.config.get_key('keyring')
        if "foo-bar'd" in keyring:
            raise
        self.category = cat
        catdir = os.path.join(keyring, cat)
        self.logger.debug(_unicode("ACTIONS: _set_category; catdir = %s") % catdir)
        return catdir


