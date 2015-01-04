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

GKEY_UID = \
'''    UID..........: %(uid)s
'''

GKEY_FINGERPRINTS = \
'''    Keyid........: %(keyid)s
      Fingerprint: %(fingerprint)s
'''


class GKEY(namedtuple('GKEY', ['nick', 'name', 'keydir', 'keys', 'fingerprint', 'uid'])):
    '''Class to hold the relavent info about a key'''

    field_types = {'nick': str, 'name': str, 'keydir': str, 'keys': list,
        'fingerprint': list, 'uid': list}
    __slots__ = ()


    @property
    def keyid(self):
        '''Keyid is a substring value of the fingerprint'''
        return ['0x' + x[-16:] for x in self.fingerprint]


    @property
    def pub_keyid(self):
        '''Keyid is a substring value of the keys fingerprints'''
        return ['0x' + x[-16:] for x in self.keys]


    @property
    def pretty_print(self):
        '''Pretty printing a GKEY'''
        gkey = {
            'name': self.name,
            'nick': self.nick,
            'keydir': self.keydir,
            }
        output = GKEY_STRING % gkey
        for uid in self.uid:
            output += GKEY_UID % {'uid': uid}
        for f in self.fingerprint:
            fingerprint = {'fingerprint': f, 'keyid': '0x' + f[-16:]}
            output += GKEY_FINGERPRINTS % fingerprint
        return output


    def update(self, result_list):
        '''Processes a results instance from a colon listing
        and mines all fingerprints found.

        @param result_list: list of pyGPG.output.GPGResult instances
            (one for each fingerprint in the list)
        @return: A new, updated GKEY instance
        '''
        fingerprints = set()
        uids = set()
        for result in result_list:
            for data in result.status.data:
                if data.name ==  "FPR":
                    fingerprints.add(data.fingerprint)
                elif data.name ==  "UID":
                    uids.add(data.user_ID)
        return self._make([self.nick, self.name, self.keydir, self.keys, list(fingerprints), sorted(uids)])


class GKEY_CHECK(namedtuple('GKEY_CHECK', ['keyid', 'revoked', 'expired', 'invalid', 'sign'])):

    __slots__ = ()
