#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - gkeys-gpg/actions.py

    Primary api interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function

import sys

if sys.version_info[0] >= 3:
    _unicode = str
else:
    _unicode = unicode


from collections import OrderedDict

from snakeoil.demandload import demandload

from gkeys.actions import Actions as gkeyActions
from gkeys.actionbase import ActionBase
from gkeys.base import Args

demandload(
    "json:load",
    "gkeys.gkey:GKEY",
    "re",
)


Action_Map = OrderedDict([
    ('sign', {
        'func': 'sign',
        'options': ['nick', 'name', 'fingerprint', ],
        'desc': '''Sign a file''',
        'long_desc': '''Sign a file with the designated gpg key.
    The default sign settings can be set in gpg.conf.  These settings can be
    overridden on the command line using the 'nick', 'name', 'fingerprint' options''',
        'example': '''gkeys-gpg --sign foo''',
        }),
    ('verify', {
        'func': 'verify',
        'options': [],
        'desc': '''File automatic download and/or verification action.''',
        'long_desc': '''File automatic download and/or verification action.
    Note: If the specified key/keyring to verify against does not contain
    the key used to sign the file.  It will Auto-search for the correct key
    in the installed keys db. And verify against the matching key.
    It will report the success/failure along with the key information used for
    the verification''',
        'example': '''$ gkeys-gpg --verify foo'''
        }),
])

Available_Actions = ['sign', 'verify']


class Actions(ActionBase):
    '''Primary API actions'''

    def __init__(self, config, output=None, logger=None):
        ActionBase.__init__(self, config, output, logger)


    def verify(self, args, argv):
        '''File verification action.
        Note: If the specified key/keyring to verify against does not contain
        the key used to sign the file.  It will Auto-search for the correct key
        in the installed keys db. And verify against the matching key.'''

        '''
        @param args: argparse.parse_args instance
        @params argv: original command line args
        '''
        key = None
        if args.dash: # stdin arg
            # data is the data that is signed and needs to be verified
            data = sys.stdin.read()
            self.logger.info("data to verify:")
            self.logger.info("stdin:\n%s\n" % data)
            if not args.nick:
                (args.name, args.nick) = self._committer_search(data.split('\n'))
                keys = self.keyhandler.key_search(args, first_match=True)
                self.logger.debug("key_search results: %s" % str(keys))
                args.category = list(keys)[0]
                catdir = self._set_category(args.category)
                self.logger.debug("Category found from key_search: %s"
                    % args.category)
                key = keys[args.category][0]

        if not args.category:
            args.category = self.config.get_key('verify_keyring')
            self.logger.debug(_unicode(
                "ACTIONS: verify; keyring category not specified, using default: %s")
                % args.category)
            catdir = self._set_category(args.category)
        if not key:
            self.logger.debug(_unicode("ACTIONS: verify; key not defined: (1)"))
            keys = self.seedhandler.load_category(args.category)
            if not keys:
                return (False, ['No installed keys found, try installkey action.'])
            key = self.seedhandler.seeds.nick_search(args.nick)
            if not key:
                self.logger.debug(_unicode("ACTIONS: verify; key not defined: (2)"))
                if args.nick:
                    self.logger.info(_unicode(
                        "Failed to find.........: %s in category: %s")
                        % (args.category, args.nick))
                args.category = self.config.get_key('verify-keyring')
                args.nick = self.config.get_key('verify-nick')
                self.logger.info(_unicode("Using config defaults..: %s %s")
                    % (args.category, args.nick))
                catdir = self._set_category(args.category)
                return self.verify(args)

        self.logger.debug(_unicode("ACTIONS: verify; catdir = %s") % catdir)
        if args.statusfd:
            self.config.defaults['gpg_defaults'] = [
                '--display-charset', 'utf-8',
                '--status-fd', args.statusfd]
        self.config.defaults['gpg_defaults'].extend(["--trust-model", "always"])
        self.logger.info("Verifying file...")
        results = self.gpg.verify_text(key, data.encode('utf-8'), args.verify)
        keyid = key.keyid[0]
        (valid, trust) = results.verified
        # TODO verify that the key it is signed with is listed as a current
        # gpg key for that dev, not an old one still in the keyring.
        # Add a setting to trigger allowing old gpg keys to validate against
        if valid:
            self.logger.info(_unicode("Verification succeeded.: %s")
                % (args.verify))
            self.logger.info(_unicode("Key info...............: %s <%s>, %s")
                % ( key.name, key.nick, keyid))
            self.logger.info(_unicode("    category, nick.....: %s %s")
                % (args.category, args.nick))
        else:
            self.logger.info(
                _unicode("Verification failed....: %s") % (args.verify))
            self.logger.info(_unicode("Key info...............: %s <%s>, %s")
                % ( key.name, key.nick, keyid))
            found, args, new_msgs = self.keyhandler.autosearch_key(args, results)
            if found:
                return self.verify(args)
        sys.stdout.write(results.output)
        sys.stderr.write('\n'.join(results.stderr_out))
        self.logger.debug("gpg stdout results: \n%s\n" %str(results.output))
        self.logger.debug("gpg returncode: \n%s\n" %str(results.returncode))
        self.logger.debug("gpg stderr results: \n%s\n" %str(results.stderr_out))
        return (results.returncode, results)


    def sign(self, args, argv):
        '''Sign a file using gnupg's gpg command, replacing the current process'''
        cmd = ['usr/bin/gpg']
        cmd.extend(argv)
        for stream in (sys.__stdout__, sys.__stderr__):
            stream.flush()

        try:
            pid = os.fork()
            if pid == 0:
                # A second fork is required in order to create an
                # "orphan" process that will be reaped by init.
                pid = os.fork()
                if pid == 0:
                    os.setsid()
                os._exit(0)

            os.waitpid(pid, 0)
            os.execv(cmd[0], cmd)
        except Exception:
            traceback.print_exc()
        finally:
            os._exit(1)


    def _committer_search(self, data):
        username = None
        nick = None
        for line in data:
            self.logger.debug("_committer_search: line: %s" % line)
            matches = re.match("committer (.*) <(.*)@.*>", line)
            if matches is not None:
                username = matches.group(1)
                nick = matches.group(2)
                self.logger.debug("_committer_search: "
                    "Commiter username, nick: %s, %s" % (username, nick))
                break
        return (username, nick)
