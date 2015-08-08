#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - config.py

    Holds configuration keys and values

    @copyright: 2012-2015 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GNU GPL2, see COPYING for details.
"""

import os

from collections import OrderedDict

from pyGPG.config import GPGConfig

from gkeys.SaneConfigParser import SaneConfigParser
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

    def __init__(self, config=None, root=None, read_configfile=False):
        """ Class initialiser """
        GPGConfig.__init__(self)

        self.logger = None
        self.root = root or ''
        self.defaults = OrderedDict(self.defaults)
        if config:
            self.defaults['config'] = config
            self.defaults['configdir'] = os.path.dirname(config)
        else:
            self._set_default_config()
        self.configparser = None
        self._add_gkey_defaults()
        if read_configfile:
            self.read_config()


    def _set_default_config(self):
            self.defaults['homedir'] = os.path.expanduser('~')
            self.defaults['userconfigdir'] = os.path.join(
                self.defaults['homedir'], '.config', 'gkeys')
            self.defaults['configdir'] = self.defaults['userconfigdir']
            self.defaults['config']= os.path.join(
                self.defaults['userconfigdir'], 'gkeys.conf')
            if not os.path.exists(self.defaults['config']):
                self.defaults['configdir'] = path([self.root, EPREFIX, '/etc/gkeys'])
                self.defaults['config'] = '%(configdir)s/gkeys.conf'

    def _add_gkey_defaults(self):
        self.defaults['gkeysdir'] = path([self.root, EPREFIX, '/var/lib/gentoo/gkeys'])
        self.defaults['keyring'] = '%(gkeysdir)s/keyrings'
        self.defaults['sign-keydir'] = '%(gkeysdir)s/sign',
        self.defaults['logdir'] = '/var/log/gkeys'
        # local directory to scan for seed files installed via ebuild, layman
        # or manual install.
        self.defaults['seedsdir'] = '%(gkeysdir)s/seeds'
        self.defaults['seeds'] = {}
        self.defaults['keyserver'] = 'pool.sks-keyservers.net'
        # NOTE: files is umask mode in octal, directories is chmod mode in octal
        self.defaults['permissions'] = {'files': '0o002', 'directories': '0o775',}
        self.defaults['seedurls'] = {}
        self.defaults['sign'] = {
            'key': 'fingerprint',
            'keydir': '~/.gkeys',
            'keyring': None,
            'type': 'clearsign',
        }
        self.defaults['verify-keyring'] = ''
        self.defaults['verify-seeds'] = {}


    def read_config(self, filename=None):
        '''Reads the config file into memory
        '''
        if "%(configdir)s" in self.defaults['config']:
            # fix the config path
            self.defaults['config'] = self.defaults['config'] \
                % {'configdir': self.defaults['configdir']}
        for key in self.defaults:
            self.defaults[key] = self._sub_(self.defaults[key])
        defaults = OrderedDict()
        # Add only the defaults we want in the configparser
        for key in ['gkeysdir', 'homedir', 'keyring', 'sign-keydir', 'logdir',
            'seedsdir', 'keyserver']:
            defaults[key] = self.defaults[key]
        if filename == None:
            filename = self.defaults['config']
        if "foo-bar'd" in filename:
            print("Config: read_config(); Configuration ERROR: filename: %s, access: %s"
                % (filename, os.access(filename, os.R_OK)))
        self.configparser = SaneConfigParser(defaults)
        self.configparser.read(filename)
        if self.configparser.has_section('base'):
            # I consider this hacky, but due to shortcomings of ConfigParser
            # we need to reset the defaults redefined in the 'base' section
            for key in self.configparser.options('base'):
                self.defaults[key] = self.configparser.get('base', key)
                defaults[key] = self.defaults[key]
        self.configparser._defaults = defaults
        for section in self.configparser.sections():
            if section == 'base':
                continue
            for key in self.configparser.options(section):
                if section not in self.defaults:
                    self.defaults[section] = {}
                self.defaults[section][key] = self.configparser.get(section, key)

    def get_key(self, key, subkey=None):
        return self._get_(key, subkey)


    def _get_(self, key, subkey=None):
        if subkey:
            if key in self.options and subkey in self.options[key]:
                return self._sub_(self.options[key][subkey])
            elif key in self.defaults and subkey in self.defaults[key]:
                return self._sub_(self.defaults[key][subkey])
            else:
                return super(GKeysConfig, self)._get_(key, subkey)
        else:
            return super(GKeysConfig, self)._get_(key, subkey)

