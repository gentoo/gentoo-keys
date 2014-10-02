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

Available_Actions = ['listseed', 'addseed', 'removeseed', 'moveseed', 'fetchseed',
            'listseedfiles', 'listkey', 'installkey', 'removekey', 'movekey',
            'installed', 'importkey', 'verify', 'checkkey']


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
                self.seeds = handler.load_seeds(args.seeds, args.seedfile)
            except ValueError:
                return ["Failed to load seed file. Consider fetching seedfiles."]
        if self.seeds:
            results = self.seeds.list(**kwargs)
        else:
            results = ''
        return ['', results]


    def fetchseed(self, args):
        '''Download the selected seed file(s)'''
        handler = SeedHandler(self.logger, self.config)
        messages = handler.fetch_seeds(args.seeds)
        self.logger.debug("ACTIONS: fetchseed; args: %s" % str(args))
        return messages


    def addseed(self, args):
        '''Add a key to the selected seed file(s)'''
        handler = SeedHandler(self.logger, self.config)
        gkeys = self.listseed(args)[1]
        if not args.nick or not args.name or not args.fingerprint:
            return ["Provide a nickname, a name and a fingerprint."]
        gkey = handler.new(args, checkgkey=True)
        if len(gkeys) == 0:
            self.logger.debug("ACTIONS: installkey; now adding gkey: %s" % str(gkey))
            success = self.seeds.add(getattr(gkey, 'nick'), gkey)
            if success:
                success = self.seeds.save()
                messages = ["Successfully added new seed."]
        else:
            messages = ["Matching seeds found in seeds file",
                "Aborting... \nMatching seeds:", gkeys]
        return messages


    def removeseed(self, args):
        '''Remove a key from the selected seed file(s)'''
        handler = SeedHandler(self.logger, self.config)
        searchkey = handler.build_gkeydict(args)
        self.logger.debug("ACTIONS: removeseed; gkey: %s" % str(searchkey))
        gkeys = self.listseed(args)[1]
        if not gkeys:
            return ["Failed to remove seed: No gkeys returned from listseed()",
                None]
        if len(gkeys) == 1:
            self.logger.debug("ACTIONS: removeseed; now deleting gkey: %s" % str(gkeys))
            success = self.seeds.delete(gkeys)
            if success:
                success = self.seeds.save()
            return ["Successfully removed seed: %s" % str(success),
                gkeys]
        elif len(gkeys):
            return ["Too many seeds found to remove", gkeys]
        return ["Failed to remove seed:", searchkey,
            "No matching seed found"]


    def moveseed(self, args):
        '''Move keys between seed files'''
        handler = SeedHandler(self.logger)
        searchkey = handler.new(args, needkeyid=False, checkintegrity=False)
        self.logger.debug("ACTIONS: moveseed; gkey: %s" % str(searchkey))
        if not self.seeds:
            self.seeds = self.load_seeds(args.seeds)
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
                % (args.seeds, str(success)), sourcekeys[0]])
            return messages
        elif len(sourcekeys):
            messages = ["Too many seeds found to move"]
            messages.extend(sourcekeys)
            return messages
        messages.append("Failed to move seed:")
        messages.append(searchkey)
        messages.append('\n')
        messages.append("Source seeds found...")
        messages.extend(sourcekeys or ["None\n"])
        messages.append("Destination seeds found...")
        messages.extend(destkeys or ["None\n"])
        return messages


    def listkey(self, args):
        '''Pretty-print the selected seed file or nick'''
        # get the desired seed
        keyresults = self.listseed(args)[1]
        if not keyresults:
            return ["No keydirs to list"]
        elif keyresults and not args.nick == '*' and self.output:
            self.output(['', keyresults], "\n Found GKEY seeds:")
        elif keyresults and self.output:
            self.output(['all'], "\n Installed seeds:")
        else:
            self.logger.info("ACTIONS: listkey; "
                "Matching seed entry not found")
            if args.nick:
                messages = ["Search failed for: %s" % args.nick]
            elif args.name:
                messages = ["Search failed for: %s" % args.name]
            else:
                messages = ["Search failed for search term"]
        # get confirmation
        # fill in code here
        keydir = self.config.get_key(args.seeds + "-keydir")
        self.logger.debug("ACTIONS: listkey; keysdir = %s" % keydir)
        self.gpg = GkeysGPG(self.config, keydir)
        results = {}
        print(" GPG output:")
        for key in keyresults:
            if not key.keydir and not args.nick == '*':
                self.logger.debug("ACTIONS: listkey; NO keydir... Ignoring")
                messages = ["Failed: No keyid's found for %s" % key.name]
            else:
                self.logger.debug("ACTIONS: listkey; listing keydir:" + str(key.keydir))
                results[key.name] = self.gpg.list_keys(key.keydir)
                if self.config.options['print_results']:
                    print(results[key.name].output)
                    self.logger.debug("data output:\n" + str(results[key.name].output))
                    messages = ["Done."]
                else:
                    return results
        return messages


    def installkey(self, args):
        '''Install a key from the seed(s)'''
        handler = SeedHandler(self.logger, self.config)
        kwargs = handler.build_gkeydict(args)
        self.logger.debug("ACTIONS: installkey; kwargs: %s" % str(kwargs))
        gkey = self.listseed(args)[1]
        if gkey:
            if gkey and not args.nick == '*' and self.output:
                self.output(['', gkey], "\n Found GKEY seeds:")
            elif gkey and self.output:
                self.output(['all'], "\n Installing seeds:")
            else:
                self.logger.info("ACTIONS: installkey; "
                    "Matching seed entry not found")
                if args.nick:
                    return ["Search failed for: %s" % args.nick]
                elif args.name:
                    return ["Search failed for: %s" % args.name]
                else:
                    return ["Search failed for search term"]
            # get confirmation
            # fill in code here
            keydir = self.config.get_key(args.seeds + "-keydir")
            self.logger.debug("ACTIONS: installkey; keysdir = %s" % keydir)
            self.gpg = GkeysGPG(self.config, keydir)
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
            return ["Completed"]
        return ["No seeds to search or install"]


    def checkkey(self, args):
        '''Check keys actions'''
        if not args.seeds:
            return ["Please specify seeds type (-s)."]
        self.logger.debug("ACTIONS: checkkey; args: %s" % str(args))
        installed_keys = self.installed(args)[1]
        keydir = self.config.get_key(args.seeds + "-keydir")
        self.logger.debug("ACTIONS: checkkey; keysdir = %s" % keydir)
        self.gpg = GkeysGPG(self.config, keydir)
        results = {}
        failed = defaultdict(list)
        self.output('', '\n Checking keys...')
        for gkey in installed_keys:
            self.logger.debug("ACTIONS: checkkey; gkey = %s" % str(gkey))
            for key in gkey.keyid:
                results[gkey.name] = self.gpg.check_keys(gkey.keydir, key)
                if results[gkey.name].expired:
                    failed['expired'].append("%s(%s): %s" % (gkey.name, gkey.nick, key))
                if results[gkey.name].revoked:
                    failed['revoked'].append("%s(%s): %s" % (gkey.name, gkey.nick, key))
                if results[gkey.name].invalid:
                    failed['invalid'].append("%s(%s): %s" % (gkey.name, gkey.nick, key))
                if not results[gkey.name].sign:
                    failed['sign'].append("%s(%s): %s " % (gkey.name, gkey.nick, key))
        if failed['expired']:
            self.output([failed['expired']], '\nExpired keys:\n')
        if failed['revoked']:
            self.output([failed['revoked']], '\nRevoked keys:\n')
        if failed['invalid']:
            self.output([failed['invalid']], '\nInvalid keys:\n')
        if failed['sign']:
            self.output([failed['sign']], '\nNo signing capabilities keys:\n')
        return ['\nFound:\n-------', 'Expired: %d\nRevoked: %d\nInvalid: %d\nNo signing capabilities: %d'
                % (len(failed['expired']), len(failed['revoked']),
                    len(failed['invalid']), len(failed['sign']))]


    def removekey(self, args):
        '''Remove an installed key'''
        if not args.nick:
            return ["Please provide a nickname or -n *"]
        handler = SeedHandler(self.logger, self.config)
        kwargs = handler.build_gkeydict(args)
        self.logger.debug("ACTIONS: addkey; kwargs: %s" % str(kwargs))
        installed_keys = self.installed(args)[1]
        for gkey in installed_keys:
            if kwargs['nick'] not in gkey.nick:
                messages = ["%s does not seem to be a valid key." % kwargs['nick']]
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
                    keydir = self.config.get_key(args.seeds + "-keydir")
                    rm_candidate = os.path.join(keydir, gkey.nick)
                    self.logger.debug("ACTIONS: removekey; keysdir = %s" % keydir)
                    if args.seeds:
                        try:
                            rmtree(rm_candidate)
                            messages = ["Done removing %s key." % kwargs['nick']]
                        except OSError:
                            messages = ["%s directory does not exist." % rm_candidate]
        return messages


    def movekey(self, args):
        '''Rename an installed key'''
        pass


    def importkey(self, args):
        '''Add a specified key to a specified keyring'''
        if args.seeds:
            keydir = self.config.get_key(args.seeds + "-keydir")
            keyring_dir = self.config.get_key("keyring")
            self.logger.debug("ACTIONS: importkey; keydir = %s" % keydir)
            self.gpg = GkeysGPG(self.config, keydir)
            handler = SeedHandler(self.logger, self.config)
            gkeys = self.listseed(args)[1]
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
                    keyring = os.path.join(keyring_dir,args.keyring + '.gpg')
                    self.gpg.add_to_keyring(gkey, keydir, keyring)
            if failed and self.output:
                self.output([failed], "\n Failed to install:")
            return ["Completed."]
        return ["No seeds to search or install"]


    def installed(self, args):
        '''Lists the installed key directories'''
        if args.seeds:
            keydir = self.config.get_key(args.seeds + "-keydir")
        else:
            return ["Please specify a seed file."]
        self.logger.debug("ACTIONS: installed; keysdir = %s" % keydir)
        installed_keys = []
        try:
            if args.nick:
                keys = [args.nick]
            else:
                keys = os.listdir(keydir)
            for key in keys:
                seed_path = os.path.join(keydir, key)
                gkey_path = os.path.join(seed_path, 'gkey.seeds')
                try:
                    with open(gkey_path, 'r') as fileseed:
                        seed = load(fileseed)
                except IOError:
                    return ["No seed file found in %s." % gkey_path, ""]
                installed_keys.append(GKEY(**seed.values()[0]))
        except OSError:
            return ["%s keydir does not exist." % keydir, ""]
        return ['Found Key/s:', installed_keys]


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
            return ['Please provide a signed file.']
        if not args.seeds:
            return ['Please specifiy type of seed file.']
        keys = self.installed(args)[1]
        if not keys:
            return ['No installed keys, try installkey action.']
        keydir = self.config.get_key(args.seeds + "-keydir")
        self.logger.debug("ACTIONS: verify; keysdir = %s" % keydir)
        self.gpg = GkeysGPG(self.config, keydir)
        filepath, signature  = args.filename, args.signature
        isurl = success = False
        if filepath.startswith('http'):
            isurl = True
            fetcher = Connector(connector_output, None, "Gentoo Keys")
            self.logger.debug("ACTIONS: verify; fetching %s signed file " % filepath)
            success, signedfile, timestamp = fetcher.fetch_file(filepath)
        else:
            filepath = os.path.abspath(filepath)
            self.logger.debug("ACTIONS: verify; local file %s" % filepath)
            success = os.path.isfile(filepath)
        if not success:
            messages = ["File %s cannot be retrieved." % filepath]
        else:
            if not signature:
                EXTENSIONS = ['.asc','.sig','.gpgsig']
                success_fetch = False
                for ext in EXTENSIONS:
                    signature = filepath + ext
                    if isurl:
                        self.logger.debug("ACTIONS: verify; fetching %s signature " % signature)
                        success_fetch, sig, timestamp = fetcher.fetch_file(signature)
                    else:
                        signature = os.path.abspath(signature)
                        self.logger.debug("ACTIONS: verify; checking %s signature " % signature)
                        success_fetch = os.path.isfile(signature)
                    if success_fetch:
                        break
            messages = []
            #TODO: use file:// uri in the future
            if isurl:
                splitfile = filepath.split('/')[-1]
                splitsig = signature.split('/')[-1]
                filepath = os.path.abspath(splitfile)
                signature = os.path.abspath(splitsig)
            self.logger.info("Verifying file...")
            for key in keys:
                results = self.gpg.verify_file(key, signature, filepath)
                keyid = key.keyid[0]
                if results.verified[0]:
                    messages = ["File %s has been successfully verified | %s (%s)." % (filepath, str(key.name), str(keyid))]
                else:
                    messages = ["File verification of %s failed | %s (%s)." % (filepath, str(key.name), str(keyid))]
        return messages


    def listseedfiles(self, args):
        '''List seed files found in the configured seed directory'''
        seedsdir = self.config.get_key('seedsdir')
        seedfile = [f for f in os.listdir(seedsdir) if f[-5:] == 'seeds']
        return {"Seed files found at path: %s\n  %s"
            % (seedsdir, "\n  ".join(seedfile)): True}
