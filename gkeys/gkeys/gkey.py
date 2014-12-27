#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - gkey.py

    Holds GKEY class and related values

    @copyright: 2012-2015 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GNU GPL2, see COPYING for details.
"""


from collections import namedtuple


GKEY_STRING = '''    ----------
    Name.........: %(name)s
    Nick.........: %(nick)s
    Keydir.......: %(keydir)s
'''

GKEY_FINGERPRINTS = \
'''    Keyid........: %(keyid)s
      Fingerprint: %(fingerprint)s
'''


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
