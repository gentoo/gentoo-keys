#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - gkeys-gpg/actions.py

    Primary api interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function

import os
import sys

if sys.version_info[0] >= 3:
    py_input = input
    _unicode = str
else:
    py_input = raw_input
    _unicode = unicode


from collections import defaultdict

from snakeoil.demandload import demandload

from gkeys.gkey import GKEY
from gkeys.checks import SPECCHECK_SUMMARY, convert_pf, convert_yn

demandload(
    "json:load",
    "gkeys.lib:GkeysGPG",
    "gkeys.seedhandler:SeedHandler",
)


EXTENSIONS = ['.sig', '.asc', '.gpg','.gpgsig']


class Actions(object):
    '''Primary API actions'''

    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger
        self.seeds = None


