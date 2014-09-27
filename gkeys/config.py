#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - config.py

    Holds configuration keys and values

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GNU GPL2, see COPYING for details.
"""

import os
import sys

# py3.2
if sys.hexversion >= 0x30200f0:
    import configparser as ConfigParser
else:
    import ConfigParser

from collections import namedtuple


from pyGPG.config import GPGConfig

from gkeys import log
from gkeys.utils import path

logger = log.logger


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

class GKeysConfig(GPGConfig):
    """ Configuration superclass which holds our gentoo-keys
    config settings for pygpg """

    def __init__(self, config=None, root=None, read_configfile=False):
        """ Class initialiser """
        GPGConfig.__init__(self)

        self.root = root or ''
        if config:
            self.defaults['config'] = config
            self.defaults['configdir'] = os.path.dirname(config)
        else:
            self.defaults['configdir'] = path([self.root, EPREFIX, '/etc/gentoo-keys'])
            self.defaults['config'] = '%(configdir)s/gkeys.conf'
        self.configparser = None
        self._add_gkey_defaults()
        if read_configfile:
            self.read_config()


    def _add_gkey_defaults(self):
        self.defaults['keysdir'] = path([self.root, EPREFIX, '/var/gentoo/gkeys'])
        self.defaults['dev-keydir'] = '%(keysdir)s/devs'
        self.defaults['rel-keydir'] = '%(keysdir)s/release'
        self.defaults['keyring'] = '%(keysdir)s/keyring'
        self.defaults['overlays-keydir'] = '%(keysdir)s/overlays'
        self.defaults['logdir'] = '%(keysdir)s/logs'
        # local directory to scan for seed files installed via ebuild, layman
        # or manual install.
        self.defaults['seedsdir'] = '%(keysdir)s/seeds'
        self.defaults['dev-seedfile'] = '%(seedsdir)s/developer.seeds'
        self.defaults['rel-seedfile'] = '%(seedsdir)s/release.seeds'
        self.defaults['dev-timestamp'] = '%(keysdir)s/.developer_seeds_timestamp'
        self.defaults['rel-timestamp'] = '%(keysdir)s/.release_seeds_timestamp'
        self.defaults['keyserver'] = 'pool.sks-keyservers.net'
        # NOTE: files is umask mode in octal, directories is chmod mode in octal
        self.defaults['permissions'] = {'files': '0o002', 'directories': '0o775',}
        self.defaults['seedurls'] = {
            'release.seeds': 'https://dev.gentoo.org/~dolsen/gkey-seeds/release.seeds',
            'developers.seeds': 'https://dev.gentoo.org/~dolsen/gkey-seeds/developer.seeds',
        }


    def read_config(self):
        '''Reads the config file into memory
        '''
        if "%(configdir)s" in self.defaults['config']:
            # fix the config path
            self.defaults['config'] = self.defaults['config'] \
                % {'configdir': self.defaults['configdir']}
        defaults = self.get_defaults()
        # remove some defaults from being entered into the configparser
        for key in ['gpg_defaults', 'only_usable', 'refetch', 'tasks']:
            defaults.pop(key)
        self.configparser = ConfigParser.ConfigParser(defaults)
        self.configparser.add_section('MAIN')
        self.configparser.read(defaults['config'])


    def get_key(self, key, subkey=None):
        return self._get_(key, subkey)


    def _get_(self, key, subkey=None):
        if subkey:
            if self.configparser.get(key, subkey):
                if logger:
                    logger.debug("Found %s in configparser... %s"
                        % (key, str(self.configparser.get(key, subkey))))
                return self._sub_(self.configparser.get(key, subkey))
            if subkey in self.options[key]:
                return self._sub_(self.options[key][subkey])
            elif subkey in self.defaults[key]:
                return self._sub_(self.defaults[key][subkey])
        elif self.configparser and self.configparser.has_option('MAIN', key):
            if logger:
                logger.debug("Found %s in configparser... %s"
                    % (key, str(self.configparser.get('MAIN', key))))
                #logger.debug("type(key)= %s"
                #    % str(type(self.configparser.get('MAIN', key))))
            return self.configparser.get('MAIN', key)
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
