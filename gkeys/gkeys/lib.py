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

# for py 2.6 compatibility
from __future__ import print_function

import os
from os.path import abspath, pardir
from os.path import join as pjoin
from shutil import rmtree

from pyGPG.gpg import GPG
from gkeys.checks import KeyChecks
from gkeys.fileops import ensure_dirs
from gkeys.seed import Seeds

class GkeysGPG(GPG):
    '''Gentoo-keys primary gpg class'''


    def __init__(self, config, basedir, logger):
        '''class init function

        @param config: GKeysConfig config instance to use
        @param keydir: string, the path to the keydir to be used
                        for all operations.
        '''
        GPG.__init__(self, config, logger)
        self.config = config
        self.basedir = basedir
        self.logger = logger
        self.keydir = None
        self.server = None


    def set_keyserver(self, server=None):
        '''Set the keyserver and add the --keyserver option to the gpg defaults
        '''
        if self.server and not server:
            return
        self.server = server or self.config['keyserver']
        self.config.options['gpg_defaults'] = self.config.defaults['gpg_defaults'][:]
        self.logger.debug("keyserver: %s" % (self.server))
        server_value = ['--keyserver', self.server]
        self.config.options['gpg_defaults'].extend(server_value)
        self.logger.debug("self.config.options['gpg_defaults']: %s"
            % (self.config.options['gpg_defaults']))
        return


    def set_keyring(self, keyring, task, importkey=False, reset=True):
        '''Sets the keyring to use as well as related task options
        '''
        self.logger.debug("keydir: %s, keyring: %s" % (self.keydir, keyring))
        if reset:
            self.config.options['tasks'][task] =  self.config.defaults['tasks'][task][:]
        # --keyring file |  Note that this adds a keyring to the current list.
        # If the intent is to use the specified keyring alone,
        # use  --keyring  along with --no-default-keyring.
        if importkey:
            task_value = ['--import-options', 'import-clean']
            self.config.options['tasks'][task].extend(task_value)
            parent_dir = abspath(pjoin(keyring, pardir))
            ensure_dirs(parent_dir,
                mode=int(self.config.get_key('permissions', 'directories'),0))
        task_value = ['--no-default-keyring', '--keyring', keyring]
        self.config.options['tasks'][task].extend(task_value)
        self.logger.debug("set_keyring: New task options: %s" %str(self.config.options['tasks'][task]))
        return


    def set_keydir(self, keydir, task, fingerprint=True, reset=True):
        self.logger.debug("basedir: %s, keydir: %s" % (self.basedir, keydir))
        self.keydir = pjoin(self.basedir, keydir)
        self.task = task
        if reset:
            self.config.options['tasks'][task] = self.config.defaults['tasks'][task][:]
        task_value = []
        if fingerprint:
            task_value.append('--fingerprint')
        task_value.extend(['--homedir', self.keydir])
        self.config.options['tasks'][task].extend(task_value)
        self.logger.debug("set_keydir: New task options: %s" %str(self.config.options['tasks'][task]))
        return


    def add_to_keyring(self, gkey, keydir, keyring):
        '''Add the specified key to the specified keyring

        @param gkey: GKEY namedtuple with
            (name, keyid/longkeyid, keydir, fingerprint)
        @param keydir: path with the specified keydir
        @param keyring: string with the specified keyring
        '''
        self.set_keydir(keydir, 'import', reset=True)
        self.set_keyring(keyring, 'import', importkey=True, reset=False)
        results = []
        self.logger.debug("LIB: import_to_keyring; name: " + gkey.name)
        self.logger.debug("** Calling runGPG with Running: gpg %s --import' for: %s"
                     % (' '.join(self.config.get_key('tasks', 'import')),
                        gkey.name))
        pubring_path = pjoin(self.keydir, gkey.keydir, 'pubring.gpg')
        result = self.runGPG(task='import', inputfile=pubring_path)
        self.logger.info('GPG return code: ' + str(result.returncode))
        results.append(result)
        print(result.stderr_out)
        return results


    def add_key(self, gkey):
        '''Add the specified key to the specified keydir

        @param gkey: GKEY namedtuple with
            (name, nick, keydir, fingerprint)
        '''
        self.config.defaults['gpg_defaults'].append('--no-permission-warning')
        self.set_keyserver()
        self.set_keydir(gkey.keydir, 'recv-keys', reset=True)
        self.set_keyring('pubring.gpg', 'recv-keys', reset=False)
        self.logger.debug("LIB: add_key; ensure dirs: " + self.keydir)
        mode = int(self.config.get_key('permissions', 'directories'),0)
        ensure_dirs(str(self.keydir), mode=mode)
        self.set_keyseedfile(trap_errors=True)
        results = []
        for fingerprint in gkey.keys:
            self.logger.debug("LIB: add_key; adding fingerprint " + fingerprint)
            self.logger.debug("** Calling runGPG with Running 'gpg %s --recv-keys %s' for: %s"
                % (' '.join(self.config.get_key('tasks', 'recv-keys')),
                    fingerprint, gkey.name))
            result = self.runGPG(task='recv-keys', inputfile=fingerprint)
            self.logger.info('GPG return code: ' + str(result.returncode))
            if result.fingerprint in gkey.keys:
                result.failed = False
                message = "Fingerprints match... Import successful: "
                message += "%s, fingerprint: %s" % (gkey.nick, fingerprint)
                message += "\n result len: %s, %s" % (len(result.fingerprint), result.fingerprint)
                message += "\n gkey len: %s, %s" % (len(gkey.fingerprint[0]), gkey.fingerprint[0])
                self.logger.info(message)
            else:
                result.failed = True
                message = "Fingerprints do not match... Import failed for "
                message += "%s, fingerprint: %s" % (gkey.nick, fingerprint)
                message += "\n result: %s" % (result.fingerprint)
                message += "\n gkey..: %s" % (str(gkey.fingerprint))
                self.logger.error(message)
            # Save the gkey seed to the installed db
            success = self.update_gkey(gkey, save=True)
            if not success:
                return []
            results.append(result)
        return results


    def del_key(self, gkey, key):
        '''Delete the specified key

        @param gkey: GKEY namedtuple with (name, nick, keydir, fingerprint)
        @param key: Fingerprint of the primary key to delete
        '''
        self.set_keydir(gkey.keydir, 'del-key', reset=True)
        self.set_keyring('pubring.gpg', 'del-key', reset=False)
        self.set_keyseedfile(refresh=True)
        self.logger.debug("LIB: del_key, gkey: %s" % str(gkey))
        self.logger.debug("LIB: del_key, key: %s" % key)
        self.logger.debug("** Calling runGPG with: 'gpg %s --delete-keys' for: %s"
            % (' '.join(self.config.get_key('tasks', 'delete-keys')), str(gkey)))
        result = self.runGPG(task='delete-keys', inputfile=key)
        self.logger.info('GPG return code: ' + str(result.returncode))
        self.update_gkey(gkey, save=True)
        return (False, [])


    def del_keydir(self, gkey):
        '''Delete the specified keydir

        @param gkey: GKEY namedtuple with (name, nick, keydir, fingerprint)
        '''
        rm_candidate = os.path.join(self.basedir, gkey.keydir)
        success = False
        messages = []
        try:
            rmtree(rm_candidate)
            messages.append("Done removing %s key." % gkey.nick)
            success = True
        except OSError:
            messages.append("%s directory does not exist or is a symbolic link." % rm_candidate)
        return (success, messages)


    def refresh_key(self, gkey):
        '''Refresh the specified key in the specified keydir

        @param key: tuple of (name, nick, keydir, fingerprint)
        @param keydir: the keydir to add the key to
        '''
        self.config.defaults['gpg_defaults'].append('--no-permission-warning')
        self.set_keyserver()
        self.set_keydir(gkey.keydir, 'refresh-keys', reset=True)
        self.set_keyring('pubring.gpg', 'refresh-keys', reset=False)
        self.set_keyseedfile(refresh=True)
        self.logger.debug("LIB: refresh_key, gkey: %s" % str(gkey))
        self.logger.debug("** Calling runGPG with Running 'gpg %s --refresh-keys' for: %s"
            % (' '.join(self.config.get_key('tasks', 'refresh-keys')), str(gkey)))
        result = self.runGPG(task='refresh-keys', inputfile='')
        self.logger.info('GPG return code: ' + str(result.returncode))
        self.update_gkey(gkey, save=True)
        return result


    def update_gkey(self, gkey, save=False):
        '''Update the specified key in the specified keydir

        @param key: tuple of (name, nick, keydir, fingerprint)
        @param keydir: the keydir to add the key to
        '''
        # Update the gkey seed and save it to the installed db
        lresults = []
        for fpr in gkey.keys:
            lresults.append(self.list_keys(gkey.keydir, fpr, colons=True))
        self.seedfile.update(gkey.update(lresults))
        if save and not self.seedfile.save():
            self.logger.error("GkeysGPG.update_gkey(); failed to save seed: " + gkey.nick)
            return False
        return True



    def list_keys(self, keydir, fingerprint=None, colons=False):
        '''List all keys in the specified keydir or
        all keys in all keydir if keydir=None

        @param keydir: the keydir to list the keys for
        @param colons: bool to enable colon listing
        '''
        if not keydir:
            self.logger.debug("LIB: list_keys(), invalid keydir parameter: %s"
                % str(keydir))
            return []
        if fingerprint:
            task = 'list-key'
            target = fingerprint
            self.set_keydir(keydir, task, fingerprint=True)
        else:
            task = 'list-keys'
            target = ''
            self.set_keydir(keydir, task, fingerprint=False)
        self.config.options['tasks'][task].extend(['--keyid-format', 'long', '--fingerprint'])
        if colons:
            task_value = ['--with-colons']
            self.config.options['tasks'][task].extend(task_value)
        self.logger.debug("** Calling runGPG with Running 'gpg %s --%s %s'"
            % (' '.join(self.config['tasks'][task]), task, target)
            )
        result = self.runGPG(task=task, inputfile=target)
        self.logger.info('GPG return code: ' + str(result.returncode))
        return result


    def check_keys(self, keydir, keyid, result=None):
        '''Check specified or all keys based on the seed type

        @param keydir: the keydir to list the keys for
        @param keyid: the keyid to check
        @param result: optional pyGPG.output.GPGResult object
        @returns: GKEY_CHECK instance
        '''
        if not result:
            result = self.list_keys(keydir, fingerprint=keyid, colons=True)
        checker = KeyChecks(self.logger, qualified_id_check=True)
        return checker.validity_checks(keydir, keyid, result)


    def speccheck(self, keydir, keyid, result=None):
        '''Check specified or all keys based on the seed type
        specifications are met.

        @param keydir: the keydir to list the keys for
        @param keyid: the keyid to check
        @param result: optional pyGPG.output.GPGResult object
        @returns: SpecCheck instance
        '''
        if not result:
            result = self.list_keys(keydir, fingerprint=keyid, colons=True)
        checker = KeyChecks(self.logger, qualified_id_check=True)
        specchecks = checker.spec_check(keydir, keyid, result)
        return specchecks


    def list_keydirs(self):
        '''List all available keydirs
        '''
        return []


    def verify_key(self, gkey):
        '''Verify the specified key from the specified keydir

        @param gkey: GKEY namedtuple with (name, keyid/longkeyid, fingerprint)
        '''
        pass


    def verify_text(self, text):
        '''Verify a text block in memory
        '''
        pass


    def verify_file(self, gkey, signature, filepath):
        '''Verify the file specified at filepath or url

        @param gkey: GKEY instance of the gpg key used to verify it
        @param signature: string with the signature file
        @param filepath: string with the path or url of the signed file
        '''
        if signature:
            self.set_keydir(gkey.keydir, 'verify', reset=True)
            self.logger.debug("** Calling runGPG with Running 'gpg %s --verify %s and %s'"
                    % (' '.join(self.config['tasks']['verify']), signature, filepath))
            results = self.runGPG(task='verify', inputfile=[signature,filepath])
        else:
            self.set_keydir(gkey.keydir, 'decrypt', reset=True)
            self.logger.debug("** Calling runGPG with Running 'gpg %s --decrypt %s'"
                    % (' '.join(self.config['tasks']['decrypt']), filepath))
            results = self.runGPG(task='decrypt', inputfile=filepath)
        keyid = gkey.keyid[0]
        if results.verified[0]:
            self.logger.info("GPG verification succeeded. Name: %s / Key: %s" % (gkey.name, keyid))
            self.logger.info("\tSignature result:" + str(results.verified))
        else:
            self.logger.debug("GPG verification failed. Name: %s / Key: %s" % (gkey.name, keyid))
            self.logger.debug("\t Signature result:"+ str(results.verified))
            self.logger.debug("LIB: verify; stderr_out:" + str(results.stderr_out))
        return results


    def set_keyseedfile(self, trap_errors=True, refresh=False):
        if not self.keydir:
            self.logger.debug("GkeysGPG.set_keyseedfile(); self.keydir error")
        self.seedfile = Seeds(pjoin(self.keydir, 'gkey.seeds'), self.config, self.logger)
        self.seedfile.load(trap_errors=trap_errors, refresh=refresh)


    def sign_file(self, gkey, mode, fingerprint, filepath):
        '''Verify the file specified at filepath or url

        @param gkey: GKEY instance
        @param mode: string of the signing task to use
        @param fingerprint: string of the fingerprint to sign with
        @param filepath: string with the path of the file to sign
        '''
        keyid = gkey.keyid[0]
        self.set_keydir(gkey.keydir, mode, reset=True)
        self.logger.debug("** Calling runGPG with Running 'gpg %s --%s %s %s'"
                % (' '.join(self.config['tasks'][mode]), mode, fingerprint, filepath))
        results = self.runGPG(task=mode, inputfile=filepath)

        if results.verified[0]:
            self.logger.info("GPG signing succeeded. Name: %s / Key: %s" % (str(gkey.name), str(keyid)))
            self.logger.info("\tSignature result:" + str(results.verified))
        else:
            self.logger.debug("GPG signing failed. Name: %s / Key: %s" % (str(gkey.name), str(keyid)))
            self.logger.debug("\t Signature result:"+ str(results.verified))
            self.logger.debug("LIB: sign; stderr_out:" + str(results.stderr_out))
        return results
