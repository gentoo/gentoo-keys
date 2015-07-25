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
    _unicode = str
else:
    _unicode = unicode


from collections import OrderedDict

from snakeoil.demandload import demandload

from gkeys.gkey import GKEY

demandload(
    "json:load",
    "gkeys.lib:GkeysGPG",
    "gkeys.seedhandler:SeedHandler",
)


EXTENSIONS = ['.sig', '.asc', '.gpg','.gpgsig']

Action_Map = OrderedDict([
    ('sign', {
        'func': 'sign',
        'options': ['nick', 'name', 'fingerprint', ],
        'desc': '''Sign a file''',
        'long_desc': '''Sign a file with the designated gpg key.
    The default sign settings can be set in gpg.conf.  These settings can be
    overridden on the command line using the 'nick', 'name', 'fingerprint' options''',
        'example': '''gkeys-gpg --sign foo''',
        }),
    ('verify', {
        'func': 'verify',
        'options': [],
        'desc': '''File automatic download and/or verification action.''',
        'long_desc': '''File automatic download and/or verification action.
    Note: If the specified key/keyring to verify against does not contain
    the key used to sign the file.  It will Auto-search for the correct key
    in the installed keys db. And verify against the matching key.
    It will report the success/failure along with the key information used for
    the verification''',
        'example': '''$ gkeys-gpg --verify foo'''
        }),
])

Available_Actions = ['sign', 'verify']


class Actions(object):
    '''Primary API actions'''

    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger
        self.seeds = None


    def verify(self, args):
        '''File verification action.
        Note: If the specified key/keyring to verify against does not contain
        the key used to sign the file.  It will Auto-search for the correct key
        in the installed keys db. And verify against the matching key.'''

        '''
        @param args: argparse.parse_args instance
        '''
        print("Made it to the --verify option :)")
        return (True, ['Completed'])

    def sign(self, args):
        '''Sign a file'''
        print("Made it to the --sign option :)")
        return (True, ['Completed'])
