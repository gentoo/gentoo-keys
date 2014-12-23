#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - config.py

    Holds configuration keys and values

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GNU GPL2, see COPYING for details.
"""

import os

from collections import OrderedDict
from collections import namedtuple

from pyGPG.config import GPGConfig

from gkeys.SaneConfigParser import SaneConfigParser
from gkeys.utils import path



# establish the eprefix, initially set so eprefixify can
# set it on install
EPREFIX = "@GENTOO_PORTAGE_EPREFIX@"

# check and set it if it wasn't
if "GENTOO_PORTAGE_EPREFIX" in EPREFIX:
    EPREFIX = ''

GKEY_STRING = '''    ----------
    Name.........: %(name)s
    Nick.........: %(nick)s
    Keydir.......: %(keydir)s
'''

GKEY_FINGERPRINTS = \
'''    Keyid........: %(keyid)s
      Fingerprint: %(fingerprint)s
'''

MAPSEEDS = { 'dev' : 'gentoodevs.seeds', 'rel': 'gentoo.seeds' }


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
            homedir = os.path.expanduser('~')
            self.defaults['configdir'] = homedir
            self.defaults['config']= os.path.join(homedir, '.gkeys.conf')
            if not os.path.exists(self.defaults['config']):
                self.defaults['configdir'] = path([self.root, EPREFIX, '/etc/gkeys'])
                self.defaults['config'] = '%(configdir)s/gkeys.conf'
        self.configparser = None
        self._add_gkey_defaults()
        if read_configfile:
            self.read_config()


    def _add_gkey_defaults(self):
        self.defaults['gkeysdir'] = path([self.root, EPREFIX, '/var/lib/gentoo/gkeys'])
        self.defaults['keyring'] = '%(gkeysdir)s/keyring'
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


    def read_config(self):
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
        for key in ['gkeysdir', 'keyring', 'sign-keydir', 'logdir', 'seedsdir',
            'keyserver']:
            defaults[key] = self.defaults[key]
        self.configparser = SaneConfigParser(defaults)
        self.configparser.read(self.defaults['config'])
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


class GKEY(namedtuple('GKEY', ['nick', 'name', 'keydir', 'fingerprint'])):
    '''Class to hold the relavent info about a key'''

    field_types = {'nick': str, 'name': str, 'keydir': str, 'fingerprint': list}
    __slots__ = ()


    @property
    def keyid(self):
        '''Keyid is a substring value of the fingerprint'''
        return ['0x' + x[-16:] for x in self.fingerprint]


    @property
    def pretty_print(self):
        '''Pretty printing a GKEY'''
        gkey = {'name': self.name, 'nick': self.nick, 'keydir': self.keydir}
        output = GKEY_STRING % gkey
        for f in self.fingerprint:
            fingerprint = {'fingerprint': f, 'keyid': '0x' + f[-16:]}
            output += GKEY_FINGERPRINTS % fingerprint
        return output


class GKEY_CHECK(namedtuple('GKEY_CHECK', ['keyid', 'revoked', 'expired', 'invalid', 'sign'])):

    __slots__ = ()
