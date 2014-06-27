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

from gkeys.lib import GkeysGPG
from gkeys.seedhandler import SeedHandler

Available_Actions = ['listseed', 'addseed', 'removeseed', 'moveseed', 'fetchseed',
            'listseedfiles', 'listkey', 'addkey', 'removekey', 'movekey',
            'installed']


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
            self.logger.debug("ACTIONS: addkey; now adding gkey: %s" % str(gkey))
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
        if not args.nick:
            return ["Too many seeds found. Consider using -n <nick> option."]
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


    def addkey(self, args):
        '''Install a key from the seed(s)'''
        if not args.nick:
            return ["Please provide a nickname or -n *"]
        handler = SeedHandler(self.logger, self.config)
        kwargs = handler.build_gkeydict(args)
        self.logger.debug("ACTIONS: addkey; kwargs: %s" % str(kwargs))
        gkey = self.listseed(args)[1]
        if gkey:
            if gkey and not args.nick == '*' and self.output:
                self.output(['', gkey], "\n Found GKEY seeds:")
            elif gkey and self.output:
                self.output(['all'], "\n Installing seeds:")
            else:
                self.logger.info("ACTIONS: addkey; "
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
            self.logger.debug("ACTIONS: addkey; keysdir = %s" % keydir)
            self.gpg = GkeysGPG(self.config, keydir)
            results = {}
            failed = []
            for key in gkey:
                self.logger.debug("ACTIONS: addkey; adding key:")
                self.logger.debug("ACTIONS: " + str(key))
                results[key.name] = self.gpg.add_key(key)
                for result in results[key.name]:
                    self.logger.debug("ACTIONS: addkey; result.failed = " +
                                      str(result.failed))
                if self.config.options['print_results']:
                    for result in results[key.name]:
                        print("key desired:", key.name, ", key added:",
                            result.username, ", succeeded:",
                            not result.failed,", fingerprint:", result.fingerprint)
                        self.logger.debug("stderr_out: " + str(result.stderr_out))
                        if result.failed:
                            failed.append(key)
            if failed and self.output:
                self.output(failed, "\n Failed to install:")
            return ["Completed"]
        return ["No seeds to search or install"]


    def removekey(self, args):
        '''Remove an installed key'''
        pass


    def movekey(self, args):
        '''Rename an installed key'''
        pass


    def installed(self, args):
        '''Lists the installed key directories'''
        pass


    def user_confirm(self, message):
        '''Prompt a user to confirm an action

        @param message: string, user promt message to display
        @return boolean: confirmation to proceed or abort
        '''
        pass


    def listseedfiles(self, args):
        '''List seed files found in the configured seed directory'''
        seedsdir = self.config.get_key('seedsdir')
        seedfile = [f for f in os.listdir(seedsdir) if f[-5:] == 'seeds']
        return {"Seed files found at path: %s\n  %s"
            % (seedsdir, "\n  ".join(seedfile)): True}
