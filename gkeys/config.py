#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - config.py

    Holds configuration keys and values

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GNU GPL2, see COPYING for details.
"""


import ConfigParser
from collections import namedtuple


from pygpg.config import GPGConfig

from gkeys.utils import path


# establish the eprefix, initially set so eprefixify can
# set it on install
EPREFIX = "@GENTOO_PORTAGE_EPREFIX@"

# check and set it if it wasn't
if "GENTOO_PORTAGE_EPREFIX" in EPREFIX:
    EPREFIX = ''



class GKeysConfig(GPGConfig):
    """ Configuration superclass which holds our gentoo-keys
    config settings for pygpg """

    def __init__ (self, config=None, root=None):
        """ Class initialiser """
        GPGConfig.__init__(self)

        self.root = root or ''
        if config:
            self.defaults['config'] = config
            self.defaults['configdir'] = os.path.dirname(config)
        else
            self.defaults['configdir'] = path([self.root, EPREFIX, '/etc/gentoo-keys'])
            self.defaults['config'] = '%(configdir)s/gkeys.conf'
        self.configparser = None

        # read our config file overrides
        self.read_config()


    def _add_gkey_defaults(self):
        self.defaults['keysdir'] = path([self.root, EPREFIX, '/var/gentoo/gkeys'])
        self.defaults['devkeydir'] = '%(keysdir)s/devs'
        self.defaults['releasekeydir'] = '%(keysdir)s/release')
        self.defaults['knownkeysfile'] = '%(keysdir)s/knownkeys'



    def read_config(self):
        '''Reads the config file into memory
        '''
        if "%(configdir)s" in self.defaults['config']:
            # fix the config path
            self.defaults['config'] = self.defaults['config'] \
                % {'configdir': self.defaults['configdir']}
        defaults = self.get_defaults()
        self.configparser = ConfigParser.ConfigParser(defaults)
        self.configparser.add_section('MAIN')
        self.configparser.read(defaults['config'])

    def _get_(self, key):
        if self.configparser and self.configparser.has_option('MAIN', key):
            return self.configparser.get('MAIN', key)
        else:
            super('GKeysConfig', self)._get_(key)


class GKEY(namedtuple('GKEY', ['name', 'keyid', 'longkeyid',
    'fingerprint', 'keyring']):
    '''Class to hold the relavent info about a key'''


