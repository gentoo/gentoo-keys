#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - seedhandler.py

    Seed handling interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

import re

from gkeys.config import (GKEY, NICK, NAME, KEYID, LONGKEYID, FINGERPRINT,
    KEY_LEN)


class SeedHandler(object):


    def __init__(self,logger):
        self.logger = logger
        self.fingerprint_re = re.compile('[0-9A-Fa-f]{40}')


    def new(self, args, needkeyid=True, checkintegrity=True):
        parts = self.build_gkeylist(args, needkeyid, checkintegrity)
        gkey = GKEY._make(parts)
        self.logger.debug("SeedHandler: new() new gkey: %s" % str(gkey))
        return gkey


    @staticmethod
    def build_gkeydict(args):
        keyinfo = {}
        for x in GKEY._fields:
            try:
                value = getattr(args, x)
                if value:
                    keyinfo[x] = value
            except AttributeError:
                pass
        return keyinfo


    def build_gkeylist(self, args, needkeyid=True, checkintegrity=True):
        keyinfo = []
        keyid_found = False
        # assume it's good until an error is found
        is_good = True
        #self.logger.debug("SeedHandler: build_gkeylist; args = %s" % str(args))
        for x in GKEY._fields:
            if GKEY.field_types[x] is str:
                try:
                    value = getattr(args, x)
                except AttributeError:
                    value = None
            elif GKEY.field_types[x] is list:
                try:
                    value = [y for y in getattr(args, x).split()]
                except AttributeError:
                    value = None
            keyinfo.append(value)
            if x in ["keyid", "longkeyid"] and value:
                keyid_found = True
        if not keyid_found and needkeyid:
            fingerprint = keyinfo[FINGERPRINT]
            if fingerprint:
                self.logger.debug('  Generate gpgkey longkeyid, Found '
                    'fingerprint in args')
                # assign it to gpgkey to prevent a possible
                # "gpgkey" undefined error
                gpgkey = ['0x' + x[-KEY_LEN['longkeyid']:] for x in fingerprint]
                keyinfo[LONGKEYID] = gpgkey
                self.logger.debug('  Generate gpgkey longkeyid, NEW '
                    'keyinfo[LONGKEYID] = %s' % str(keyinfo[LONGKEYID]))
            else:
                gpgkey = 'Missing or Bad fingerprint from command line args'
                is_good = False
            if not keyinfo[LONGKEYID]:
                self.logger.error('ERROR in seed creation info for: %s, %s'
                    %(keyinfo[NICK], keyinfo[NAME]))
                self.logger.error('  A valid keyid, longkeyid or fingerprint '
                    'was not found for %s : gpgkey = %s'
                    %(keyinfo[NAME], gpgkey))
                is_good = False
        if is_good:
            if keyinfo[FINGERPRINT]: # fingerprints exist check
                is_ok = self._check_fingerprint_integrity(keyinfo)
                is_match = self._check_id_fingerprint_match(keyinfo)
                if not is_ok or not is_match:
                    is_good = False
        if is_good:
            return keyinfo
        return None


    def _check_id_fingerprint_match(self, keyinfo):
        # assume it's good until found an error is found
        is_good = True
        for x in [KEYID, LONGKEYID]:
            # skip blank id field
            if not keyinfo[x]:
                continue
            for y in keyinfo[x]:
                index = len(y.lstrip('0x'))
                if y.lstrip('0x').upper() not in \
                        [x[-index:].upper() for x in keyinfo[FINGERPRINT]]:
                    self.logger.error('ERROR in ldap info for: %s, %s'
                        %(keyinfo[NICK], keyinfo[NAME]))
                    self.logger.error('  ' + str(keyinfo))
                    self.logger.error('  GPGKey id %s not found in the '
                        % y.lstrip('0x') + 'listed fingerprint(s)')
                    is_good = False
        return is_good


    def _check_fingerprint_integrity(self, keyinfo):
        # assume it's good until an error is found
        is_good = True
        for x in keyinfo[FINGERPRINT]:
            # check fingerprint integrity
            if len(x) != 40:
                self.logger.error('ERROR in keyinfo for: %s, %s'
                    %(keyinfo[NICK], keyinfo[NAME]))
                self.logger.error('  GPGKey incorrect fingerprint ' +
                    'length (%s) for fingerprint: %s' %(len(x), x))
                is_good = False
                continue
            if not self.fingerprint_re.match(x):
                self.logger.error('ERROR in keyinfo info for: %s, %s'
                    %(keyinfo[NICK], keyinfo[NAME]))
                self.logger.error('  GPGKey: Non hexadecimal digits in ' +
                    'fingerprint for fingerprint: ' + x)
                is_good = False
        return is_good
