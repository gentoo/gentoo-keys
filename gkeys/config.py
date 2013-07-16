#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - config.py

    Holds configuration keys and values

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GNU GPL2, see COPYING for details.
"""

import os
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



class GKeysConfig(GPGConfig):
    """ Configuration superclass which holds our gentoo-keys
    config settings for pygpg """

    def __init__ (self, config=None, root=None, read_configfile=False):
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
        if read_configfile:
            self.read_config()


    def _add_gkey_defaults(self):
        self.defaults['keysdir'] = path([self.root, EPREFIX, '/var/gentoo/gkeys'])
        self.defaults['dev-keydir'] = '%(keysdir)s/devs'
        self.defaults['release-keydir'] = '%(keysdir)s/release'
        self.defaults['overlays-keydir'] = '%(keysdir)s/overlays'
        self.defaults['known-keysfile'] = '%(keysdir)s/knownkeys'
        self.defaults['release-seedfile'] = '%(configdir)s/release.seeds'
        self.defaults['dev-seedfile'] = '%(configdir)s/developer.seeds'



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
        if self.configparser and self.configparser.has_option('MAIN', key):
            if logger:
                logger.debug("Found %s in configparser... %s"
                    % (key, str(self.configparser.get('MAIN', key))))
                #logger.debug("type(key)= %s"
                #    % str(type(self.configparser.get('MAIN', key))))
            return self.configparser.get('MAIN', key)
        else:
            return super(GKeysConfig, self)._get_(key, subkey)


class GKEY(namedtuple('GKEY', ['nick', 'name', 'keyid', 'longkeyid',
    'keyring', 'fingerprint'])):
    '''Class to hold the relavent info about a key'''

    field_types = {'nick': str, 'name': str, 'keyid': list,
        'longkeyid': list, 'keyring': str, 'fingerprint': list}
    field_separator = "|"
    list_separator = ":"
    __slots__ = ()

    def _packed_values(self):
        '''Returns a list of the field values'''
        v = []
        for f in self._fields:
            v.append(self._pack(f))
        return v

    @property
    def packed_string(self):
        '''Returns a separator joined string of the field values'''
        return self.field_separator.join([x for x in self._packed_values()])

    def _unpack_string(self, packed_data):
        '''Returns a list of the separator joined string of the field values'''
        values = []
        data = packed_data.split(self.field_separator)
        for x in self._fields:
            values.append(self._unpack(x, data.pop(0)))
        return values

    def _pack(self, field):
        '''pack field data into a string'''
        if self.field_types[field] == str:
            return getattr(self, field)
        elif self.field_types[field] == list:
            info = getattr(self, field)
            if info:
                return self.list_separator.join(info)
            else:
                # force an empty list to None
                return 'None'
        else:
            raise "ERROR packing %s" %str(getattr(self, field))

    def _unpack(self, field, data):
        '''unpack field data to the desired type'''
        if self.field_types[field] == str:
            result = data
            if result == 'None':
                result = None
        else:
            if data == 'None':
                # make it an empty list
                result = []
            else:
                result = data.split(self.list_separator)
        return result

    def make_packed(self, packed_string):
        '''Creates a new instance of Gkey from the packed
        value string

        @param packed_string: string of data separated by field_separator
        @return new GKEY instance containing the data
        '''
        return GKEY._make(self._unpack_string(packed_string))
