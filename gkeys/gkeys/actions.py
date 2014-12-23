#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - actions.py

    Primary api interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function

import os

from collections import defaultdict
from json import load
from shutil import rmtree
from sslfetch.connections import Connector

from gkeys.lib import GkeysGPG
from gkeys.seedhandler import SeedHandler
from gkeys.config import GKEY
from gkeys.checks import SPECCHECK_SUMMARY, convert_pf, convert_yn

Available_Actions = ['listcats', 'listseed', 'addseed', 'removeseed', 'moveseed', 'fetchseed',
            'listseedfiles', 'listkey', 'installkey', 'removekey', 'movekey',
            'installed', 'importkey', 'verify', 'checkkey', 'sign', 'speccheck',
            'refreshkey']

Action_Options = {
    'listcats': [],
    'listseed': ['nick', 'name', 'keydir', 'fingerprint', 'seedfile', '1file'],
    'addseed': ['nick', 'name', 'keydir', 'fingerprint', 'seedfile'],
    'removeseed': ['nick', 'name', 'keydir', 'fingerprint', 'seedfile'],
    'moveseed': ['nick', 'name', 'keydir', 'fingerprint', 'seedfile', 'dest'],
    'fetchseed': ['nick', 'name', 'keydir', 'fingerprint', 'seedfile'],
    'listseedfiles': [],
    'listkey': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring', 'gpgsearch', 'keyid'],
    'installkey': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring', 'seedfile', '1file'],
    'removekey': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring'],
    'movekey': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring', 'dest'],
    'installed': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring'],
    'importkey': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring'],
    'verify': ['dest', 'nick', 'name', 'keydir', 'fingerprint', 'category', '1file', 'signature', 'keyring', 'timestamp'],
    'checkkey': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring', 'keyid'],
    'sign': ['nick', 'name', 'keydir', 'fingerprint', 'file', 'keyring'],
    'speccheck': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring', 'keyid'],
    'refreshkey': ['nick', 'name', 'keydir', 'fingerprint', 'category', 'keyring', 'keyid'],
}


class Actions(object):
    '''Primary API actions'''

    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger
        self.seeds = None


    def listseed(self, args):
        '''Pretty-print the selected seed file(s)'''
        handler = SeedHandler(self.logger, self.config)
        kwargs = handler.build_gkeydict(args)
        self.logger.debug("ACTIONS: listseed; kwargs: %s" % str(kwargs))
        if not self.seeds:
            try:
                self.seeds = handler.load_seeds(args.seedfile, args.filename)
            except ValueError:
                return (False, ["Failed to load seed file. Consider fetching seedfiles."])
        if self.seeds:
            results = self.seeds.list(**kwargs)
        else:
            results = ''
        return (True, ['', results])


    def fetchseed(self, args):
        '''Download the selected seed file(s)'''
        self.logger.debug("ACTIONS: fetchseed; args: %s" % str(args))
        handler = SeedHandler(self.logger, self.config)
        success, messages = handler.fetch_seeds(args.seedfile, args, self.verify)

        messages.append("")
        messages.append("Fetch operation completed")
        return (False not in success, messages)


    def addseed(self, args):
        '''Add or replace a key in the selected seed file(s)'''
        handler = SeedHandler(self.logger, self.config)
        gkeys = self.listseed(args)[1]
        if not args.nick or not args.name or not args.fingerprint:
            return (False, ["Provide a nickname, a name and a fingerprint."])
        gkey = handler.new(args, checkgkey=True)
        if not gkey:
            return (False, ["Failed to create a valid GKEY instance.",
                "Check for invalid data entries"])
        if len(gkeys) == 0:
            self.logger.debug("ACTIONS: installkey; now adding gkey: %s" % str(gkey))
            success = self.seeds.add(getattr(gkey, 'nick'), gkey)
            if success:
                success = self.seeds.save()
                messages = ["Successfully added new seed."]
        else:
            messages = ["Matching seeds found in seeds file",
                "Aborting... \nMatching seeds:", gkeys]
            success = False
        return (success, messages)


    def removeseed(self, args):
        '''Remove a key from the selected seed file(s)'''
        gkeys = self.listseed(args)[1]
        if not gkeys:
            return (False, ["Failed to remove seed: No gkeys returned from listseed()",
                []])
        if len(gkeys) == 1:
            self.logger.debug("ACTIONS: removeseed; now deleting gkey: %s" % str(gkeys))
            success = self.seeds.delete(gkeys[0])
            if success:
                success = self.seeds.save()
            return (success, ["Successfully removed seed: %s" % str(success),
                gkeys])
        elif len(gkeys):
            return (False, ["Too many seeds found to remove", gkeys])
        return (False, ["Failed to remove seed:", args,
            "No matching seed found"])


    def moveseed(self, args):
        '''Move keys between seed files'''
        handler = SeedHandler(self.logger)
        searchkey = handler.new(args, needkeyid=False, checkintegrity=False)
        self.logger.debug("ACTIONS: moveseed; gkey: %s" % str(searchkey))
        if not self.seeds:
            self.seeds = self.load_seeds(args.category)
        kwargs = handler.build_gkeydict(args)
        sourcekeys = self.seeds.list(**kwargs)
        dest = self.load_seeds(args.destination)
        destkeys = dest.list(**kwargs)
        messages = []
        if len(sourcekeys) == 1 and destkeys == []:
            self.logger.debug("ACTIONS: moveseed; now adding destination gkey: %s"
                % str(sourcekeys[0]))
            success = dest.add(sourcekeys[0])
            self.logger.debug("ACTIONS: moveseed; success: %s" %str(success))
            self.logger.debug("ACTIONS: moveseed; now deleting sourcekey: %s" % str(sourcekeys[0]))
            success = self.seeds.delete(sourcekeys[0])
            if success:
                success = dest.save()
                self.logger.debug("ACTIONS: moveseed; destination saved... %s" %str(success))
                success = self.seeds.save()
            messages.extend(["Successfully Moved %s seed: %s"
                % (args.category, str(success)), sourcekeys[0]])
            return (success, messages)
        elif len(sourcekeys):
            messages = ["Too many seeds found to move"]
            messages.extend(sourcekeys)
            return (False, messages)
        messages.append("Failed to move seed:")
        messages.append(searchkey)
        messages.append('\n')
        messages.append("Source seeds found...")
        messages.extend(sourcekeys or ["None\n"])
        messages.append("Destination seeds found...")
        messages.extend(destkeys or ["None\n"])
        return (False, messages)


    def listkey(self, args):
        '''Pretty-print the selected seed file or nick'''
        # get confirmation
        # fill in code here
        if not args.category:
            args.category = 'gentoo'
        keyring = self.config.get_key('keyring')
        catdir = os.path.join(keyring, args.category)
        self.logger.debug("ACTIONS: listkey; catdir = %s" % catdir)
        self.gpg = GkeysGPG(self.config, catdir)
        handler = SeedHandler(self.logger, self.config)
        if args.keydir:
            self.gpg.set_keydir(args.keydir, "list-keys")
            self.gpg.set_keyseedfile()
            seeds = self.gpg.seedfile
        else:
            seeds = handler.load_category(args.category)
        results = {}
        success = []
        messages = []
        if args.gpgsearch:
            keyresults = seeds.seeds
            # pick any key
            key = keyresults[sorted(keyresults)[0]]
            result = self.gpg.list_keys(key.keydir, args.gpgsearch)
            # now split the results and reverse lookup the gkey
            lines = result.output.split('\n')
            while lines:
                # determine the end of the first key listing
                index = lines.index('')
                keyinfo = lines[:index]
                # trim off the first keys info
                lines = lines[index + 1:]
                # make sure it is a key listing
                if len(keyinfo) < 2:
                    break
                # get the fingerprint from the line
                fpr = keyinfo[1].split('= ')[1]
                # search for the matching gkey
                kwargs = {'keydir': args.keydir, 'fingerprint': [fpr]}
                keyresults = seeds.list(**kwargs)
                # list the results
                for key in sorted(keyresults):
                    ls, lr = self._list_it(key, '\n'.join(keyinfo))
                    success.append(ls)
                    results[key.name] = lr
            messages = ["Done."]
        else:
            kwargs = handler.build_gkeydict(args)
            keyresults = seeds.list(**kwargs)
            for key in sorted(keyresults):
                result = self.gpg.list_keys(key.keydir, key.fingerprint)
                ls, lr = self._list_it(key, result.output)
                success.append(ls)
                results[key.name] = lr
                messages = ["Done."]

        if not messages:
            messages = ['No results found meeting criteria', "Did you specify -n foo or -n '*'"]
        return (False not in success, messages)


    def _list_it(self, key, result, print_key=True):
        self.logger.debug("ACTIONS: _list_it; listing key:" + str(key.nick))
        if self.config.options['print_results']:
            if print_key:
                print()
                print("Nick.....:", key.nick)
                print("Name.....:", key.name)
                print("Keydir...:", key.keydir)
            c = 0
            for line in result.split('\n'):
                if c == 0:
                    print("Gpg info.:", line)
                else:
                    print("          ", line)
                c += 1
            self.logger.debug("data output:\n" + str(result))
        return (True, result)


    def installkey(self, args):
        '''Install a key from the seed(s)'''
        self.logger.debug("ACTIONS: installkey; args: %s" % str(args))
        success, gkey = self.listseed(args)[1]
        if gkey:
            if gkey and not args.nick == '*' and self.output:
                self.output(['', gkey], "\n Found GKEY seeds:")
            elif gkey and self.output:
                self.output(['all'], "\n Installing seeds:")
            else:
                self.logger.info("ACTIONS: installkey; "
                    "Matching seed entry not found")
                if args.nick:
                    return (False, ["Search failed for: %s" % args.nick])
                elif args.name:
                    return (False, ["Search failed for: %s" % args.name])
                else:
                    return (False, ["Search failed for search term"])
            # get confirmation
            # fill in code here
            keyring = self.config.get_key('keyring')
            catdir = os.path.join(keyring, args.seedfile)
            self.logger.debug("ACTIONS: installkey; catdir = %s" % catdir)
            self.gpg = GkeysGPG(self.config, catdir)
            results = {}
            failed = []
            for key in gkey:
                self.logger.debug("ACTIONS: installkey; adding key:")
                self.logger.debug("ACTIONS: " + str(key))
                results[key.name] = self.gpg.add_key(key)
                for result in results[key.name]:
                    self.logger.debug("ACTIONS: installkey; result.failed = " +
                                      str(result.failed))
                if self.config.options['print_results']:
                    for result in results[key.name]:
                        print("key desired:", key.name, ", key added:",
                            result.username, ", succeeded:",
                            not result.failed, ", fingerprint:", result.fingerprint)
                        self.logger.debug("stderr_out: " + str(result.stderr_out))
                        if result.failed:
                            failed.append(key)
            if failed and self.output:
                self.output([failed], "\n Failed to install:")
            if failed:
                success = False
            return (success, ["Completed"])
        return (success, ["No seeds to search or install"])


    def checkkey(self, args):
        '''Check keys actions'''
        if not args.category:
            return (False, ["Please specify seeds type."])
        self.logger.debug("ACTIONS: checkkey; args: %s" % str(args))
        handler = SeedHandler(self.logger, self.config)
        seeds = handler.load_category(args.category)
        keyring = self.config.get_key('keyring')
        catdir = os.path.join(keyring, args.category)
        self.logger.debug("ACTIONS: checkkey; catdir = %s" % catdir)
        self.gpg = GkeysGPG(self.config, catdir)
        results = {}
        failed = defaultdict(list)
        kwargs = handler.build_gkeydict(args)
        keyresults = seeds.list(**kwargs)
        self.output('', '\n Checking keys...')
        for gkey in sorted(keyresults):
            self.logger.info("Checking key %s, %s" % (gkey.nick, gkey.keyid))
            self.output('',
                "\n  %s, %s: %s" % (gkey.nick, gkey.name, ', '.join(gkey.keyid)) +
                "\n  ==============================================")
            self.logger.debug("ACTIONS: checkkey; gkey = %s" % str(gkey))
            for key in gkey.keyid:
                results[gkey.name] = self.gpg.check_keys(gkey.keydir, key)
                if results[gkey.name].expired:
                    failed['expired'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key))
                if results[gkey.name].revoked:
                    failed['revoked'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key))
                if results[gkey.name].invalid:
                    failed['invalid'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key))
                if not results[gkey.name].sign:
                    failed['sign'].append("%s <%s>: %s " % (gkey.name, gkey.nick, key))
        if failed['expired']:
            self.output([failed['expired']], '\n Expired keys:\n')
        if failed['revoked']:
            self.output([failed['revoked']], '\n Revoked keys:\n')
        if failed['invalid']:
            self.output([failed['invalid']], '\n Invalid keys:\n')
        if failed['sign']:
            self.output([failed['sign']], '\n No signing capable subkeys:\n')
        return (len(failed) <1,
            ['\nFound:\n-------', 'Expired: %d' % len(failed['expired']),
                'Revoked: %d' % len(failed['revoked']),
                'Invalid: %d' % len(failed['invalid']),
                'No signing capable subkeys: %d' % len(failed['sign'])
            ])


    def speccheck(self, args):
        '''Check keys actions'''
        if not args.category:
            return (False, ["Please specify seeds type."])
        self.logger.debug("ACTIONS: speccheck; args: %s" % str(args))
        handler = SeedHandler(self.logger, self.config)
        seeds = handler.load_category(args.category)
        keyring = self.config.get_key('keyring')
        catdir = os.path.join(keyring, args.category)
        self.logger.debug("ACTIONS: speccheck; catdir = %s" % catdir)
        self.gpg = GkeysGPG(self.config, catdir)
        results = {}
        failed = defaultdict(list)
        kwargs = handler.build_gkeydict(args)
        keyresults = seeds.list(**kwargs)
        self.output('', '\n Checking keys...')
        for gkey in sorted(keyresults):
            self.logger.info("Checking key %s, %s" % (gkey.nick, gkey.keyid))
            self.output('',
                "\n  %s, %s: %s" % (gkey.nick, gkey.name, ', '.join(gkey.keyid)) +
                "\n  ==============================================")
            self.logger.debug("ACTIONS: speccheck; gkey = %s" % str(gkey))
            for key in gkey.keyid:
                results = self.gpg.speccheck(gkey.keydir, key)
                for g in results:
                    pub_pass = {}
                    for key in results[g]:
                        self.output('', key.pretty_print())

                        if key.key is "PUB":
                            pub_pass = {
                                'key': key,
                                'pub': key.passed_spec,
                                'sign': False,
                                'encrypt': False,
                                'auth': False,
                                'signs': [],
                                'encrypts': [],
                                'authens': [],
                                'final': False,
                            }
                        if key.key is "SUB":
                            if key.sign_capable and key.passed_spec:
                                pub_pass['signs'].append(key.passed_spec)
                                pub_pass['sign'] = True
                            if key.encrypt_capable:
                                pub_pass['encrypts'].append(key.passed_spec)
                                pub_pass['encrypt'] = True
                            if key.capabilities == 'a':
                                pub_pass['authens'].append(key.passed_spec)
                                if key.passed_spec:
                                    pub_pass['auth'] = True
                        validity = key.validity.split(',')[0]
                        if not key.expire and not 'r' in validity:
                            failed['expired'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key.fingerprint))
                        if 'r' in validity:
                            failed['revoked'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key.fingerprint))
                        if 'i' in validity:
                            failed['invalid'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key.fingerprint))
                        if key.capabilities not in ['a', 'e']:
                            if not key.algo:
                                failed['algo'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key.fingerprint))
                            if not key.bits:
                                failed['bits'].append("%s <%s>: %s" % (gkey.name, gkey.nick, key.fingerprint))
                        if "Warning" in key.expire_reason:
                            failed['warn'].append("%s <%s>: %s " % (gkey.name, gkey.nick, key.fingerprint))
                    if True in pub_pass['signs']:
                        pub_pass['sign'] = True
                    if True in pub_pass['encrypts']:
                        pub_pass['encrypt'] = True
                    if not pub_pass['sign']:
                        failed['sign'].append("%s <%s>: %s" % (gkey.name, gkey.nick, pub_pass['key'].fingerprint))
                    if not pub_pass['encrypt']:
                        failed['encrypt'].append("%s <%s>: %s" % (gkey.name, gkey.nick, pub_pass['key'].fingerprint))
                    spec = "%s <%s>: %s" % (gkey.name, gkey.nick, pub_pass['key'].fingerprint)
                    for k in ['pub', 'sign']:
                        if pub_pass[k]:
                            pub_pass['final'] = True
                        else:
                            pub_pass['final'] = False
                            break
                    if pub_pass['final']:
                        if spec not in failed['spec-approved']:
                            failed['spec-approved'].append(spec)
                    else:
                        if spec not in failed['spec']:
                            failed['spec'].append(spec)
                    sdata = convert_pf(pub_pass, ['pub', 'sign', 'final'])
                    sdata = convert_yn(sdata, ['auth', 'encrypt'])
                    self.output('', SPECCHECK_SUMMARY % sdata)

        if failed['revoked']:
            self.output([sorted(set(failed['revoked']))], '\n Revoked keys:')
        if failed['invalid']:
            self.output([sorted(set(failed['invalid']))], '\n Invalid keys:')
        if failed['sign']:
            self.output([sorted(set(failed['sign']))], '\n No signing capable subkey:')
        if failed['encrypt']:
            self.output([sorted(set(failed['encrypt']))], '\n No Encryption capable subkey (Notice only):')
        if failed['algo']:
            self.output([sorted(set(failed['algo']))], '\n Incorrect Algorithm:')
        if failed['bits']:
            self.output([sorted(set(failed['bits']))], '\n Incorrect bit length:')
        if failed['expired']:
            self.output([sorted(set(failed['expired']))], '\n Expiry keys:')
        if failed['warn']:
            self.output([sorted(set(failed['warn']))], '\n Expiry Warnings:')
        if failed['spec']:
            self.output([sorted(set(failed['spec']))], '\n Failed to pass SPEC requirements:')
        if failed['spec-approved']:
            self.output([sorted(set(failed['spec-approved']))], '\n SPEC Approved:')

        return (len(failed) <1,
            ['\nFound Failures:\n-------',
                'Revoked................: %d' % len(set(failed['revoked'])),
                'Invalid................: %d' % len(set(failed['invalid'])),
                'No Signing subkey......: %d' % len(set(failed['sign'])),
                'No Encryption subkey...: %d' % len(set(failed['encrypt'])),
                'Algorithm..............: %d' % len(set(failed['algo'])),
                'Bit length.............: %d' % len(set(failed['bits'])),
                'Expiry.................: %d' % len(set(failed['expired'])),
                'Expiry Warnings........: %d' % len(set(failed['warn'])),
                'SPEC requirements......: %d' % len(set(failed['spec'])),
                '=============================',
                'SPEC Approved..........: %d' % len(set(failed['spec-approved'])),
            ])


    def removekey(self, args):
        '''Remove an installed key'''
        if not args.nick:
            return (False, ["Please provide a nickname or -n *"])
        handler = SeedHandler(self.logger, self.config)
        kwargs = handler.build_gkeydict(args)
        self.logger.debug("ACTIONS: addkey; kwargs: %s" % str(kwargs))
        success, installed_keys = self.installed(args)[1]
        for gkey in installed_keys:
            if kwargs['nick'] not in gkey.nick:
                messages = ["%s does not seem to be a valid key." % kwargs['nick']]
                success = False
            else:
                self.output(['', [gkey]], '\n Found GKEY seed:')
                ans = raw_input("Do you really want to remove %s?[y/n]: "
                                % kwargs['nick']).lower()
                while ans not in ["yes", "y", "no", "n"]:
                    ans = raw_input("Do you really want to remove %s?[y/n]: "
                                    % kwargs['nick']).lower()
                if ans in ["no", "n"]:
                    messages = ["Key removal aborted... Nothing to be done."]
                else:
                    keyring = self.config.get_key('keyring')
                    catdir = os.path.join(keyring, args.category)
                    rm_candidate = os.path.join(catdir, gkey.nick)
                    self.logger.debug("ACTIONS: removekey; catdir = %s" % catdir)
                    if args.category:
                        try:
                            rmtree(rm_candidate)
                            messages = ["Done removing %s key." % kwargs['nick']]
                        except OSError:
                            messages = ["%s directory does not exist." % rm_candidate]
                            success = False
        return (success, messages)


    def movekey(self, args):
        '''Rename an installed key'''
        return (False, [])


    def importkey(self, args):
        '''Add a specified key to a specified keyring'''
        if args.category:
            keyring = self.config.get_key('keyring')
            catdir = os.path.join(keyring, args.category)
            keyring_dir = self.config.get_key("keyring")
            self.logger.debug("ACTIONS: importkey; catdir = %s" % catdir)
            self.gpg = GkeysGPG(self.config, catdir)
            success, gkeys = self.listseed(args)[1]
            results = {}
            failed = []
            print("Importing specified keys to keyring.")
            for gkey in gkeys:
                self.logger.debug("ACTIONS: importkey; adding key: %s", gkey.name)
                results[gkey.name] = self.gpg.add_key(gkey)
                if self.config.options['print_results']:
                    for result in results[gkey.name]:
                        print("key desired:", gkey.name, ", key added:",
                            result.username, ", succeeded:",
                            not result.failed, ", fingerprint:", result.fingerprint)
                        self.logger.debug("stderr_out: " + str(result.stderr_out))
                        if result.failed:
                            self.logger.debug("ACTIONS: importkey; result.failed = " + str(result.failed))
                            failed.append(gkey)
                if not results[gkey.name][0].failed:
                    print("Importing: ", gkey.name)
                    self.logger.debug("ACTIONS: importkey; importing key: %s", gkey.name)
                    _keyring = os.path.join(catdir, args.keyring + '.gpg')
                    self.gpg.add_to_keyring(gkey, catdir, _keyring)
            if failed and self.output:
                self.output([failed], "\n Failed to install:")
            if len(failed):
                success = False
            return (success, ["Completed."])
        return (False, ["No seeds to search or install",
            "You must specify a category"])


    def installed(self, args):
        '''Lists the installed key directories'''
        if args.category:
            keyring = self.config.get_key('keyring')
            catdir = os.path.join(keyring, args.category)
        else:
            return (False, ["Please specify a category."])
        self.logger.debug("ACTIONS: installed; catdir = %s" % catdir)
        installed_keys = []
        try:
            if args.nick:
                keys = [args.nick]
            else:
                keys = os.listdir(catdir)
            for key in keys:
                seed_path = os.path.join(catdir, key)
                gkey_path = os.path.join(seed_path, 'gkey.seeds')
                seed = None
                try:
                    with open(gkey_path, 'r') as fileseed:
                        seed = load(fileseed)
                except IOError:
                    return ["No seed file found in %s." % gkey_path, ""]
                if seed:
                    for val in list(seed.values()):
                        installed_keys.append(GKEY(**val))
        except OSError:
            return (False, ["%s directory does not exist." % catdir, ""])
        return (True, ['Found Key(s):', installed_keys])


    def user_confirm(self, message):
        '''Prompt a user to confirm an action

        @param message: string, user promt message to display
        @return boolean: confirmation to proceed or abort
        '''
        pass


    def verify(self, args):
        '''File verification action'''
        connector_output = {
             'info': self.logger.debug,
             'error': self.logger.error,
             'kwargs-info': {},
             'kwargs-error': {},
        }
        if not args.filename:
            return (False, ['Please provide a signed file.'])
        if not args.category:
            args.category = 'gentoo'
        (success, data) = self.installed(args)
        keys = data[1]
        if not keys:
            return (False, ['No installed keys found, try installkey action.'])
        keyring = self.config.get_key('keyring')
        catdir = os.path.join(keyring, args.category)
        self.logger.debug("ACTIONS: verify; catdir = %s" % catdir)
        self.gpg = GkeysGPG(self.config, catdir)
        filepath, signature  = args.filename, args.signature
        timestamp_path = None
        isurl = success = verified = False
        if filepath.startswith('http'):
            isurl = True
            url = filepath
            filepath = args.destination
            # a bit hackish, but save it to current directory
            # with download file name
            if not filepath:
                filepath = url.split('/')[-1]
                self.logger.debug("ACTIONS: verify; destination filepath was "
                    "not supplied, using current directory ./%s" % filepath)
        if args.timestamp:
            timestamp_path = filepath + ".timestamp"
        if isurl:
            from sslfetch.connections import Connector
            connector_output = {
                 'info': self.logger.info,
                 'debug': self.logger.debug,
                 'error': self.logger.error,
                 'kwargs-info': {},
                 'kwargs-debug': {},
                 'kwargs-error': {},
            }
            fetcher = Connector(connector_output, None, "Gentoo Keys")
            self.logger.debug("ACTIONS: verify; fetching %s signed file " % filepath)
            self.logger.debug("ACTIONS: verify; timestamp path: %s" % timestamp_path)
            success, signedfile, timestamp = fetcher.fetch_file(url, filepath, timestamp_path)
        else:
            filepath = os.path.abspath(filepath)
            self.logger.debug("ACTIONS: verify; local file %s" % filepath)
            success = os.path.isfile(filepath)
        if not success:
            messages = ["File %s cannot be retrieved." % filepath]
        else:
            if not signature:
                EXTENSIONS = ['.sig', '.asc', 'gpg','.gpgsig']
                success_fetch = False
                for ext in EXTENSIONS:
                    sig_path = filepath + ext
                    if isurl:
                        signature = url + ext
                        self.logger.debug("ACTIONS: verify; fetching %s signature " % signature)
                        success_fetch, sig, timestamp = fetcher.fetch_file(signature, sig_path)
                    else:
                        signature = filepath + ext
                        signature = os.path.abspath(signature)
                        self.logger.debug("ACTIONS: verify; checking %s signature " % signature)
                        success_fetch = os.path.isfile(signature)
                    if success_fetch:
                        break
            else:
                sig_path = signature
            messages = []
            self.logger.info("Verifying file...")
            verified = False
            # get correct key to use
            use_gkey = self.config.get_key('seedurls', 'gkey')
            for key in keys:
                if key.nick == use_gkey:
                    break
            results = self.gpg.verify_file(key, sig_path, filepath)
            keyid = key.keyid[0]
            (valid, trust) = results.verified
            if valid:
                verified = True
                messages = ["Verification succeeded.: %s" % (filepath),
                    "Key info...............: %s <%s>, %s"
                    % ( key.name, key.nick,keyid)]
            else:
                messages = ["Verification failed.....:" % (filepath),
                    "Key info................: %s <%s>, %s"
                    % ( key.name, key.nick,keyid)]
        return (verified, messages)


    def listcats(self, args):
        '''List seed file definitions found in the config'''
        seeds = list(self.config.get_key('seeds'))
        return (True, {"Categories/Seedfiles defined: %s\n"
            % (",  ".join(seeds)): True})


    def listseedfiles(self, args):
        '''List seed files found in the configured seed directory'''
        seedsdir = self.config.get_key('seedsdir')
        seedfile = [f for f in os.listdir(seedsdir) if f[-5:] == 'seeds']
        return (True, {"Seed files found at path: %s\n  %s"
            % (seedsdir, "\n  ".join(seedfile)): True})


    def sign(self, args):
        '''Sign a file'''
        if not args.filename:
            return (False, ['Please provide a file to sign.'])

        if not args.nick:
            args.nick = self.config.get_key("sign", "nick")
        if isinstance(args.nick, str):
            nicks = [args.nick]
        else:
            nicks = args.nick
        # load our installed signing keys db
        handler = SeedHandler(self.logger, self.config)
        self.seeds = handler.load_category('sign', nicks)
        if not self.seeds.seeds:
            return (False, ['No installed keys, try installkey action.', ''])
        basedir = self.config.get_key("sign-keydir")
        keydir  = self.config.get_key("sign", "keydir")
        task = self.config.get_key("sign", "type")
        keyring = self.config.get_key("sign", "keyring")

        self.config.options['gpg_defaults'] = ['--status-fd', '2']

        self.logger.debug("ACTIONS: sign; keydir = %s" % keydir)

        self.gpg = GkeysGPG(self.config, basedir)
        self.gpg.set_keydir(keydir, task)
        if keyring not in ['', None]:
            self.gpg.set_keyring(keyring, task)
        msgs = []
        success = []
        for fname in args.filename:
            results = self.gpg.sign(task, None, fname)
            verified, trust = results.verified
            if not results.verified[0]:
                msgs.extend(
                    ['Failed Signature for %s verified: %s, trust: %s'
                        % (fname, verified, trust), 'GPG output:', "\n".join(results.stderr_out)]
                )
                success.append(False)
            else:
                msgs.extend(
                    ['Signature result for: %s -- verified: %s, trust: %s'
                        % (fname, verified, trust)] #, 'GPG output:', "\n".join(results.stderr_out)]
                )
                success.append(True)
        return (False not in success, ['', msgs])


    def refreshkey(self, args):
        '''Calls gpg with the --refresh-keys option
        for in place updates of the installed keys'''
        if not args.category:
            return (False, ["Please specify seeds type."])
        self.logger.debug("ACTIONS: refreshkey; args: %s" % str(args))
        handler = SeedHandler(self.logger, self.config)
        seeds = handler.load_category(args.category)
        keyring = self.config.get_key('keyring')
        catdir = os.path.join(keyring, args.category)
        self.logger.debug("ACTIONS: refreshkey; catdir = %s" % catdir)
        self.gpg = GkeysGPG(self.config, catdir)
        results = {}
        kwargs = handler.build_gkeydict(args)
        keyresults = seeds.list(**kwargs)
        self.output('', '\n Refreshig keys...')
        for gkey in sorted(keyresults):
            self.logger.info("Refreshig key %s, %s" % (gkey.nick, gkey.keyid))
            self.output('', "  %s: %s" % (gkey.name, ', '.join(gkey.keyid)))
            #self.output('', "  ===============")
            self.logger.debug("ACTIONS: refreshkey; gkey = %s" % str(gkey))
            results[gkey.keydir] = self.gpg.refresh_key(gkey)
        return (True, ['Completed'])




