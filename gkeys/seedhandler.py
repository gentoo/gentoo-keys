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
    KEYLEN_MAP)


class SeedHandler(object):


    def __init__(self,logger):
        self.logger = logger
        self.fingerprint_re = re.compile('[0-9A-Fa-f]{40}')
        self.finerprint_re2 = re.compile('[0-9A-Fa-f]{4}( [0-9A-Fa-f]{4}){9}')


    def new(self, args, needkeyid=True, checkintegrity=True):
        parts = self.build_gkeylist(args, needkeyid, checkintegrity)
        if parts:
            gkey = GKEY._make(parts)
            self.logger.debug("SeedHandler: new() new gkey: %s" % str(gkey))
        else:
            self.logger.debug("SeedHandler: new() FAILED to et parts from: %s"
                % str(args))
            return None
        return gkey


    @staticmethod
    def build_gkeydict(args):
        keyinfo = {}
        for attr in GKEY._fields:
            try:
                value = getattr(args, attr)
                if value:
                    keyinfo[attr] = value
            except AttributeError:
                pass
        return keyinfo


    def build_gkeylist(self, args, needkeyid=True, checkintegrity=True):
        keyinfo = []
        keyid_found = False
        # assume it's good until an error is found
        is_good = True
        #self.logger.debug("SeedHandler: build_gkeylist; args = %s" % str(args))
        for attr in GKEY._fields:
            if GKEY.field_types[attr] is str:
                try:
                    value = getattr(args, attr)
                except AttributeError:
                    value = None
            elif GKEY.field_types[attr] is list:
                try:
                    values = [y for y in getattr(args, attr).split(':')]
                    value = [v.replace(' ', '') for v in values]
                except AttributeError:
                    value = None
            keyinfo.append(value)
            if attr in ["keyid", "longkeyid"] and value:
                keyid_found = True
        if not keyid_found and needkeyid:
            fingerprint = keyinfo[FINGERPRINT]
            if fingerprint:
                self.logger.debug('  Generate gpgkey longkeyid, Found '
                    'fingerprint in args')
                # assign it to gpgkey to prevent a possible
                # "gpgkey" undefined error
                gpgkey = ['0x' + x[-KEYLEN_MAP['longkeyid']:] for x in fingerprint]
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
                    self.logger.error('ERROR in keyinfo for: %s, %s'
                        %(keyinfo[NICK], keyinfo[NAME]))
                    self.logger.error('  ' + str(keyinfo))
                    self.logger.error('  GPGKey id %s not found in the '
                        % y.lstrip('0x') + 'listed fingerprint(s)')
                    is_good = False
            ids = 0
            for x in [KEYID, LONGKEYID]:
                if keyinfo[x]:
                    ids = ids + len(keyinfo[x])
            if ids != len(keyinfo[FINGERPRINT]):
                self.logger.error('ERROR in keyinfo for: %s, %s'
                    %(keyinfo[NICK], keyinfo[NAME]))
                self.logger.error('  ' + str(keyinfo))
                self.logger.error('  GPGKey the number of ids %d DO NOT match '
                    'the number of listed fingerprint(s), {%s,%s}, %s'
                    % (ids, keyinfo[KEYID], keyinfo[LONGKEYID], keyinfo[FINGERPRINT]))
                is_good = False

        return is_good


    def _check_fingerprint_integrity(self, keyinfo):
        # assume it's good until an error is found
        is_good = True
        for fingerprint in keyinfo[FINGERPRINT]:
            # check fingerprint integrity
            if len(fingerprint) != 40:
                self.logger.error('ERROR in keyinfo for: %s, %s'
                    %(keyinfo[NICK], keyinfo[NAME]))
                self.logger.error('  GPGKey incorrect fingerprint ' +
                    'length (%s) for fingerprint: %s' %(len(fingerprint), fingerprint))
                is_good = False
                continue
            if not self.fingerprint_re.match(fingerprint):
                self.logger.error('ERROR in keyinfo info for: %s, %s'
                    %(keyinfo[NICK], keyinfo[NAME]))
                self.logger.error('  GPGKey: Non hexadecimal digits in ' +
                    'fingerprint for fingerprint: ' + fingerprint)
                is_good = False
        return is_good
