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

from os.path import join as pjoin

from pygpg.gpg import GPG
from gkeys.log import logger


class GkeysGPG(GPG):
    '''Gentoo-keys primary gpg class'''


    def __init__(self, config, keydir):
        '''class init function

        @param config: GKeysConfig config instance to use
        @param keyring: string, the path to the keydir to be used
                        for all operations.
        '''
        GPG.__init__(self, config)
        self.config = config
        self.keydir = keydir


    def add_key(self, gkey):
        '''Add the specified key to the specified keyring

        @param gkey: GKEY namedtuple with
            (name, keyid/longkeyid, keyring, fingerprint,)
        '''
        logger.debug("keydir: %s, keyring: %s" % (self.keydir, gkey.keyring))
        keypath = pjoin(self.keydir, gkey.keyring)
        # --keyring file |  Note that this adds a keyring to the current list.
        # If the intent is to use the specified keyring alone,
        # use  --keyring  along with --no-default-keyring.
        self.config['tasks']['recv-keys'] = [
            '--no-default-keyring', '--keyring', keypath,
            ]
        # prefer the longkeyid if available
        #logger.debug("LIB: add_key; keyids %s, %s"
        #    % (str(gkey.longkeyid), str(gkey.keyid)))
        if gkey.longkeyid != []:
            keyids = gkey.longkeyid
        #    logger.debug("LIB: add_key; found gkey.longkeyid", keyids, type(gkey.longkeyid)
        elif gkey.keyid != []:
            keyids = gkey.keyid
        #    logger.debug("LIB: add_key; found gkey.keyid" + str(keyids))
        results = []
        for keyid in keyids:
            logger.debug("LIB: add_key; final keyids" + keyid)
            logger.debug("** Calling runGPG with Running 'gpg %s --recv-keys %s' for: %s"
                % (' '.join(self.config['tasks']['recv-keys']),
                    keyid, gkey.name)
                )
            result = self.runGPG(task='recv-keys', inputfile=keyid)
            logger.info('GPG return code: ' + str(result.returncode))
            if result.fingerprint in gkey.fingerprint:
                result.failed = False
                message = "Fingerprints match... Import successful: "
                message += "key: %s" %keyid
                message += "\n    result len: %s, %s" %(len(result.fingerprint), result.fingerprint)
                message += "\n    gkey len: %s, %s" %(len(gkey.fingerprint[0]), gkey.fingerprint[0])
                logger.info(message)
            else:
                result.failed = True
                message = "Fingerprints do not match... Import failed for "
                message += "key: %s" %keyid
                message += "\n     result:   %s" %(result.fingerprint)
                message += "\n     gkey..: %s" %(str(gkey.fingerprint))
                logger.error(message)
            results.append(result)
            print result.stderr_out
        return results


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

