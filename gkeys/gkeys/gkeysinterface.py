'''Gkeys comsumer app API interface'''


import os

from snakeoil.demandload import demandload

from gkeys.config import GKeysConfig
from gkeys.gkey import GKEY

demandload(
    "gkeys:log",
    "gkeys.lib:GkeysGPG",
    "gkeys.seedhandler:SeedHandler",
)


class GkeysInterface(object):
    '''High level class to hold and operate our gkeys GkeysGPG instance'''

    def __init__(self, namespace, root='/', config=None,
        logger=None, loglevel='DEBUG'):
        '''GkeysInterface init

        @param namespace: string of the logging namespace setting to use
        @param root: string of the root path to initialize with, default is '/'
        @param logger: optional logging instance, if undefiined, it
            will use it's gkeys logger.
        @param loglevel: string one of {'CRITICAL', 'DEBUG', 'ERROR', 'FATAL',
            'INFO', 'NOTSET', 'WARN', 'WARNING'}
        '''
        self.root = root
        self.namespace = namespace
        self.config = config or GKeysConfig(root=root, read_configfile=True)
        self.logger = logger or log.logger or log.set_logger(
            namespace=namespace,
            logpath=self.config.get_key('logdir'),
            level=loglevel)
        self.gpg = None
        self.handler = None


    def keyid_search(self, keyid):
        '''Searches for a keyid in the installed keyrings

        @param keyid: string of the longkeyid to search for
        @returns dictionary of  {category: [GKEY, ...]}
        '''
        results = {}
        for cat in list(self.config.get_key('seeds')):
            self.handler.load_category(cat)
            found = self.handler.key_search({'keyid': keyid,}, ['keyid'])
            if found:
                if cat in results:
                    results[cat].extend(found)
                else:
                    results[cat] = found
        return results


    def verify_file(self, filepath, category='gentoo', nick='snapshot',
            strict=False):
        '''One stop action to verify a file.

        If the first gpg verification fails, it will auto-search
        for the correct key to validate against.
        @param filepath: path of the file to verify
        @param category: string, optional keyring category, default is 'gentoo'
        @param nick: string, optional keyring nick, default is 'snapshot'
        @param strict: boolean toggles off the auto-search if the category/nick
            supplied fail
        @return (bool, bool)  (verification pass/fail, file had a signature)
        '''
        if not self.handler:
            self.handler = SeedHandler(self.logger, self.config)
        keys = self.handler.load_category(category)
        if not keys:
            self.logger.warn('No installed keys found, try installing keys.')
            return False
        key = self.handler.seeds.nick_search(nick)
        if not key:
            self.logger.debug("Failed to find.........: %s in category: %s"
                % (category, nick))
            category = self.config.get_key('verify-keyring')
            nick = self.config.get_key('verify-nick')
            self.logger.debug("Using config defaults..: %s %s"
                % (category, nick))
            return self.verify_file(filepath, category, nick)

        keyrings = self.config.get_key('keyring')
        catdir = os.path.join(keyrings, category)
        self.logger.debug("ACTIONS: verify; catdir = %s" % catdir)
        self.gpg = GkeysGPG(self.config, catdir, self.logger)
        results = self.gpg.verify_file(key, None, filepath)

        (valid, trust) = results.verified
        if valid:
            return True, True
        self.logger.debug("Verification failed....: %s" % (filepath))
        self.logger.debug("Key info...............: %s <%s>, %s"
            % ( key.name, key.nick, key.keyid))
        has_no_pubkey, s_keyid = results.no_pubkey
        if has_no_pubkey and s_keyid and not strict:
            self.logger.debug("Auto-searching for key.: 0x%s" % s_keyid)
        elif not s_keyid or strict:
            return False, has_no_pubkey
        keys = self.keyid_search(s_keyid)
        for cat in list(keys):
            for key in keys[cat]:
                if key and key.nick:
                    if isinstance(key, GKEY):
                        self.gpg.basedir = os.path.join(keyrings, cat)
                        results = self.gpg.verify_file(key, None, filepath)
                        (valid, trust) = results.verified
                        if valid:
                            return True, True

        self.logger.debug("Failed to find gpg key.: 0x%s" % s_keyid)
        return False, False

