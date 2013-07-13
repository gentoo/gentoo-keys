#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - actions.py

    Primary api interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""


from gkeys.config import GKEY
from gkeys.lib import GkeysGPG
from gkeys.seed import Seeds





class Actions(object):
    '''Primary api actions'''

    def __init__(self, config, output, logger=None):
        self.config = config
        self.output = output
        self.logger = logger
        self.seeds = None


    @staticmethod
    def build_gkeydict(args):
        keyinfo = {}
        for x in GKEY._fields:
            try:
                value = getattr(args, x)
                if value:
                    keyinfo[x] = value
            except AttributeError:
                pass
        return keyinfo


    @staticmethod
    def build_gkeylist(args):
        keyinfo = []
        for x in GKEY._fields:
            try:
                keyinfo.append(getattr(args, x))
            except AttributeError:
                keyinfo.append(None)
        return keyinfo


    def load_seeds(self, filename):
        if not filename:
            self.logger.debug("ACTIONS: load_seeds; no filename to load: "
            "%s" % filename)
            return None
        filepath = self.config.get_key(filename + "-seedfile")
        self.logger.debug("ACTIONS: load_seeds; seeds filepath to load: "
            "%s" % filepath)
        seeds = Seeds()
        seeds.load(filepath)
        return seeds


    def listseed(self, args):
        '''Action listseed method'''
        kwargs = self.build_gkeydict(args)
        self.logger.debug("ACTIONS: listseed; kwargs: %s" % str(kwargs))
        if not self.seeds:
            self.seeds = self.load_seeds(args.seeds)
        if self.seeds:
            results = self.seeds.list(**kwargs)
            return results
        return None


    def addseed(self, args):
        '''Action addseed method'''
        parts = self.build_gkeylist(args)
        gkey = GKEY._make(parts)
        self.logger.debug("ACTIONS: addseed; new gkey: %s" % str(gkey))
        gkeys = self.listseed(args)
        if len(gkeys) == 0:
            self.logger.debug("ACTIONS: addkey; now adding gkey: %s" % str(gkey))
            success = self.seeds.add(gkey)
            if success:
                success = self.seeds.save()
                return ["Successfully Added new seed: %s" % str(success), gkey]
        else:
            messages = ["Matching seeds found in seeds file",
                "Aborting... \nMatching seeds:"]
            messages.extend(gkeys)
            return messages


    def removeseed(self, args):
        '''Action removeseed method'''
        parts = self.build_gkeylist(args)
        searchkey = GKEY._make(parts)
        self.logger.debug("ACTIONS: removeseed; gkey: %s" % str(searchkey))
        gkeys = self.listseed(args)
        if len(gkeys) == 1:
            self.logger.debug("ACTIONS: removeseed; now deleting gkey: %s" % str(gkeys[0]))
            success = self.seeds.delete(gkeys[0])
            if success:
                success = self.seeds.save()
            return ["Successfully Removed seed: %s" % str(success),
                gkeys[0]]
        elif len(gkeys):
            messages = ["Too many seeds found to remove"]
            messages.extend(gkeys)
            return messages
        return ["Failed to Remove seed:", searchkey,
            "No matching seed found"]


    def moveseed(self, args):
        '''Action moveseed method'''
        parts = self.build_gkeylist(args)
        searchkey = GKEY._make(parts)
        self.logger.debug("ACTIONS: moveseed; gkey: %s" % str(searchkey))
        if not self.seeds:
            self.seeds = self.load_seeds(args.seeds)
        kwargs = self.build_gkeydict(args)
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
        messages.append("Failed to Move seed:")
        messages.append(searchkey)
        messages.append('\n')
        messages.append("Source seeds found...")
        messages.extend(sourcekeys or ["None\n"])
        messages.append("Destination seeds found...")
        messages.extend(destkeys or ["None\n"])
        return messages


    def listkey(self, args):
        '''Action listskey method'''
        self.seeds = self.load_seeds(args.seeds)
        if self.seeds:
            kwargs = self.build_gkeydict(args)
            # get the desired seed
            keyresults = self.seeds.list(**kwargs)
            if keyresults and not args.nick == '*':
                self.output(keyresults, "\n Found GKEY seeds:")
            elif keyresults:
                self.output(['all'], "\n Installed seeds:")
            else:
                self.logger.info("ACTIONS: listkey; "
                    "Matching seed entry not found")
                if args.nick:
                    return {"Search failed for: %s" % args.nick: False}
                elif args.name:
                    return {"Search failed for: %s" % args.name: False}
                else:
                    return {"Search failed for search term": False}
            # get confirmation
            # fill in code here
            keydir = self.config.get_key(args.seeds + "-keydir")
            self.logger.debug("ACTIONS: addkey; keysdir = %s" % keydir)
            self.gpg = GkeysGPG(self.config, keydir)
            results = {}
            #failed = []
            for key in keyresults:
                if not key.keyring and not args.nick == '*':
                    self.logger.debug("ACTIONS: listkey; NO keyring... Ignoring")
                    return {"Failed: No keyid's found for %s" % key.name : ''}
                self.logger.debug("ACTIONS: listkey; listing keyring:")
                self.logger.debug("ACTIONS: " + str(key.keyring))
                results[key.name] = self.gpg.list_keys(key.keyring)
                for result in results[key.name]:
                    self.logger.debug("ACTIONS: listkey; result.failed = " +
                        str(result.failed))
                if self.config.options['print_results']:
                    for result in results[key.name]:
                        print("key desired:", key.name, ", keyring listed:",
                            result.username, ", keyid:", result.keyid,
                            ", fingerprint:", result.fingerprint)
                        self.logger.debug("stderr_out: " + str(result.stderr_out))
        return {"No keyrings to list": False}


    def addkey(self, args):
        '''Action addkey method'''
        kwargs = self.build_gkeydict(args)
        self.logger.debug("ACTIONS: listseed; kwargs: %s" % str(kwargs))
        self.seeds = self.load_seeds(args.seeds)
        if self.seeds:
            # get the desired seed
            keyresults = self.seeds.list(**kwargs)
            if keyresults and not args.nick == '*':
                self.output(keyresults, "\n Found GKEY seeds:")
            elif keyresults:
                self.output(['all'], "\n Installing seeds:")
            else:
                self.logger.info("ACTIONS: addkey; "
                    "Matching seed entry not found")
                if args.nick:
                    return {"Search failed for: %s" % args.nick: False}
                elif args.name:
                    return {"Search failed for: %s" % args.name: False}
                else:
                    return {"Search failed for search term": False}
            # get confirmation
            # fill in code here
            keydir = self.config.get_key(args.seeds + "-keydir")
            self.logger.debug("ACTIONS: addkey; keysdir = %s" % keydir)
            self.gpg = GkeysGPG(self.config, keydir)
            results = {}
            failed = []
            for key in keyresults:
                if not key.keyid and not key.longkeyid and not args.nick == '*':
                    self.logger.debug("ACTIONS: addkey; NO key id's to add... Ignoring")
                    return {"Failed: No keyid's found for %s" % key.name : ''}
                elif not key.keyid and not key.longkeyid:
                    print("No keyid's found for:", key.nick, key.name, "Skipping...")
                    failed.append(key)
                    continue
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
                            not result.failed, ", keyid:", result.keyid,
                            ", fingerprint:", result.fingerprint)
                        self.logger.debug("stderr_out: " + str(result.stderr_out))
                        if result.failed:
                            failed.append(key)
            if failed:
                self.output(failed, "\n Failed to install:")
            return {'Completed'}
        return {"No seeds to search or install": False}


    def removekey(self, args):
        '''Action removekey method'''
        pass


    def movekey(self, args):
        '''Action movekey method'''
        pass


    def user_confirm(self, message):
        '''Get input from the user to confirm to proceed
        with the desired action

        @param message: string, user promt message to display
        @return boolean: confirmation to proceed or abort
        '''
        pass

