#
#-*- coding:utf-8 -*-

"""
    Gentoo-Keys - gkeygen/checks.py

    Primary key checks module
    @copyright: 2014 by Brian Dolbec <dolsen@gentoo.org>
    @license: GNU GPL2, see COPYING for details
"""


from gkeys.config import GKEY_CHECK
from gkeys.log import logger


# Default glep 63 minimum gpg key specification
TEST_SPEC = {
    'bits': {
        'DSA': 2048,
        'RSA': 2048,
        },
    'expire': 36,      # in months
    'subkeys': {        # warning/error mode
        'encryption': {
            'mode': 'notice',
            'expire': -1,  # -1 is the primary key expirery
            },
        'sign': {
            'mode': 'error',
            'expire': 12,
            },
        },
    'type': ['DSA', 'RSA'],
    'version': 4,
}


class KeyChecks(object):
    '''Primary gpg key validation and glep spec checks class'''

    def __init__(self, spec=TEST_SPEC):
        '''@param spec: optional gpg specification to test against
                        Defaults to TEST_SPEC

        '''
        self.spec = spec


    def validity_checks(self, keydir, keyid, result):
        '''Check the specified result based on the seed type

        @param keydir: the keydir to list the keys for
        @param keyid: the keyid to check
        @param result: pyGPG.output.GPGResult object
        @returns: GKEY_CHECK instance
        '''
        revoked = expired = invalid = sign = False
        for data in result.status.data:
            if data.name ==  "PUB":
                if data.long_keyid == keyid[2:]:
                    # check if revoked
                    if 'r' in data.validity:
                        revoked = True
                        logger.debug("ERROR in key %s : revoked" % data.long_keyid)
                        break
                    # if primary key expired, all subkeys expire
                    if 'e' in data.validity:
                        expired = True
                        logger.debug("ERROR in key %s : expired" % data.long_keyid)
                        break
                    # check if invalid
                    if 'i' in data.validity:
                        invalid = True
                        logger.debug("ERROR in key %s : invalid" % data.long_keyid)
                        break
            if data.name == "SUB":
                if data.long_keyid == keyid[2:]:
                    # check if invalid
                    if 'i' in data.validity:
                        logger.debug("WARNING in subkey %s : invalid" % data.long_keyid)
                        continue
                    # check if expired
                    if 'e' in data.validity:
                        logger.debug("WARNING in subkey %s : expired" % data.long_keyid)
                        continue
                    # check if revoked
                    if 'r' in data.validity:
                        logger.debug("WARNING in subkey %s : revoked" % data.long_keyid)
                        continue
                    # check if subkey has signing capabilities
                    if 's' in data.key_capabilities:
                        sign = True
                        logger.debug("INFO subkey %s : subkey signing capabilities" % data.long_keyid)
        return GKEY_CHECK(keyid, revoked, expired, invalid, sign)


    def glep_check(self, keydir, keyid, result):
        '''Performs the minimum specifications checks on the key'''
        pass


