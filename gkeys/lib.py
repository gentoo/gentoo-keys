#
#-*- coding:utf-8 -*-

'''Gentoo-keys - lib.py
This is gentoo-keys superclass which wraps the pyGPG lib
with gentoo-keys specific convienience functions.

 Distributed under the terms of the GNU General Public License v2

 Copyright:
             (c) 2011 Brian Dolbec
             Distributed under the terms of the GNU General Public License v2

 Author(s):
             Brian Dolbec <dolsen@gentoo.org>

'''


from pygpg.gpg import GPG


class GkeysGPG(GPG):
    '''Gentoo-keys primary gpg class'''


    def __init__(self, config):
        '''class init function

        @param config: GKeysConfig config instance to use
        '''
        GPG.__init__(self, config)
        self.config = config


    def add_key(self, gkey):
        '''Add the specified key to the specified keyring

        @param gkey: GKEY namedtuple with (name, keyid/longkeyid, fingerprint)
        '''
        pass


    def del_key(self, gkey, keyring):
        '''Delete the specified key to the specified keyring

        @param gkey: GKEY namedtuple with (name, keyid/longkeyid, fingerprint)
        '''
        pass


    def del_keyring(self, keyring):
        '''Delete the specified key to the specified keyring
        '''
        pass


    def update_key(self, gkey, keyring):
        '''Update the specified key in the specified keyring

        @param key: tuple of (name, keyid, fingerprint)
        @param keyring: the keyring to add the key to
        '''
        pass


    def list_keys(self, keyring=None):
        '''List all keys in the specified keyring or
        all key in all keyrings if keyring=None

        @param keyring: the keyring to add the key to
        '''
        pass


    def list_keyrings(self):
        '''List all available keyrings
        '''
        pass


    def verify_key(self, gkey):
        '''verify the specified key from the specified keyring

        @param gkey: GKEY namedtuple with (name, keyid/longkeyid, fingerprint)
        '''
        pass


    def verify_text(self, text):
        '''Verify a text block in memory
        '''
        pass


    def verify_file(self, filepath):
        '''Verify the file specified at filepath
        '''
        pass

