#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - cli.py

    Command line interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function


import argparse
import sys

from gkeys import log
from gkeys.log import log_levels, set_logger

from gkeys import config
from gkeys import seed
from gkeys import lib

from gkeys.config import GKeysConfig, GKEY
from gkeys.seed import Seeds
from gkeys.lib import GkeysGPG




class Main(object):
    '''Main command line interface class'''


    def __init__(self, root=None, config=None, print_results=True):
        """ Main class init function.

        @param root: string, root path to use
        """
        self.root = root or "/"
        self.config = config or GKeysConfig(root=root)
        self.print_results = print_results
        self.args = None
        self.seeds = None


    def __call__(self, args=None):
        if args:
            self.run(self.parse_args(args))
        else:
            self.run(self.parse_args(sys.argv[1:]))


    def parse_args(self, args):
        '''Parse a list of aruments

        @param args: list
        @returns argparse.Namespace object
        '''
        #logger.debug('MAIN: parse_args; args: %s' % args)
        actions = ['listseed', 'addseed', 'removeseed', 'moveseed', 'listkey',
            'addkey', 'removekey', 'movekey']
        parser = argparse.ArgumentParser(
            prog='gkeys',
            description='Gentoo-keys manager program',
            epilog='''Caution: adding untrusted keys to these keyrings can
                be hazardous to your system!''')
        # actions
        parser.add_argument('action', choices=actions, nargs='?',
            default='listseeds', help='Add to seed file or keyring')
        # options
        parser.add_argument('-c', '--config', dest='config', default=None,
            help='The path to an alternate config file')
        parser.add_argument('-d', '--dest', dest='destination', default=None,
            help='The destination seed file or keyring for move, copy operations')
        parser.add_argument('-f', '--fingerprint', dest='fingerprint', default=None,
            help='The fingerprint of the the key')
        parser.add_argument('-N', '--name', dest='name', default=None,
            help='The name of the the key')
        parser.add_argument('-n', '--nick', dest='nick', default=None,
            help='The nick associated with the the key')
        parser.add_argument('-k', '--keyid', dest='keyid', default=None,
            help='The keyid of the the key')
        parser.add_argument('-l', '--longkeyid', dest='longkeyid', default=None,
            help='The longkeyid of the the key')
        parser.add_argument('-r', '--keyring',
            choices=['release', 'dev', 'overlays'], dest='keyring', default=None,
            help='The keyring to use or update')
        parser.add_argument('-s', '--seeds',
            choices=['release', 'dev'], dest='seeds', default=None,
            help='The seeds file to use or update')
        parser.add_argument('-S', '--seedfile', dest='seedfile', default=None,
            help='The seedfile path to use')
        parser.add_argument('-D', '--debug', default='DEBUG',
            choices=list(log_levels),
            help='The logging level to set for the logfile')

        return parser.parse_args(args)


    def run(self, args):
        '''Run the args passed in

        @param args: list or argparse.Namespace object
        '''
        global logger
        message = None
        if not args:
            message = "Main: run; invalid args argument passed in"
        if isinstance(args, list):
            args = self.parse_args(args)
        if args.config:
            self.config.defaults['config'] = args.config
        # now make it load the config file
        self.config.read_config()

        # establish our logger and update it in the imported files
        logger = set_logger('gkeys', self.config['logdir'], args.debug)
        config.logger = logger
        seed.logger = logger
        lib.logger = logger

        if message:
            logger.error(message)

        # now that we have a logger, record the alternate config setting
        if args.config:
            logger.debug("Main: run; Found alternate config request: %s"
                % args.config)

        # run the action
        func = getattr(self, '_action_%s' % args.action)
        logger.debug('Main: run; Found action: %s' % args.action)
        results = func(args)
        if not results:
            print("No results found.  Check your configuration and that the",
                "seed file exists.")
            return
        if self.print_results and 'done' not in list(results):
            self.output_results(results, '\n Gkey task results:')
            print()


    @staticmethod
    def output_results(results, header):
        # super simple output for the time being
        print(header)
        print("\n".join([str(x) for x in results]))


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


    def _load_seeds(self, filename):
        if not filename:
            return None
        filepath = self.config.get_key(filename + "-seedfile")
        logger.debug("MAIN: _load_seeds; seeds filepath to load: "
            "%s" % filepath)
        seeds = Seeds()
        seeds.load(filepath)
        return seeds


    def _action_listseed(self, args):
        '''Action listseed method'''
        kwargs = self.build_gkeydict(args)
        logger.debug("MAIN: _action_listseed; kwargs: %s" % str(kwargs))
        if not self.seeds:
            self.seeds = self._load_seeds(args.seeds)
        if self.seeds:
            results = self.seeds.list(**kwargs)
            return results
        return None


    def _action_addseed(self, args):
        '''Action addseed method'''
        parts = self.build_gkeylist(args)
        gkey = GKEY._make(parts)
        logger.debug("MAIN: _action_addseed; new gkey: %s" % str(gkey))
        gkeys = self._action_listseed(args)
        if len(gkeys) == 0:
            logger.debug("MAIN: _action_addkey; now adding gkey: %s" % str(gkey))
            success = self.seeds.add(gkey)
            if success:
                success = self.seeds.save()
                return ["Successfully Added new seed: %s" % str(success), gkey]
        else:
            messages = ["Matching seeds found in seeds file",
                "Aborting... \nMatching seeds:"]
            messages.extend(gkeys)
            return messages


    def _action_removeseed(self, args):
        '''Action removeseed method'''
        parts = self.build_gkeylist(args)
        searchkey = GKEY._make(parts)
        logger.debug("MAIN: _action_removeseed; gkey: %s" % str(searchkey))
        gkeys = self._action_listseed(args)
        if len(gkeys) == 1:
            logger.debug("MAIN: _action_removeseed; now deleting gkey: %s" % str(gkeys[0]))
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


    def _action_moveseed(self, args):
        '''Action moveseed method'''
        parts = self.build_gkeylist(args)
        searchkey = GKEY._make(parts)
        logger.debug("MAIN: _action_moveseed; gkey: %s" % str(searchkey))
        if not self.seeds:
            self.seeds = self._load_seeds(args.seeds)
        kwargs = self.build_gkeydict(args)
        sourcekeys = self.seeds.list(**kwargs)
        dest = self._load_seeds(args.destination)
        destkeys = dest.list(**kwargs)
        messages = []
        if len(sourcekeys) == 1 and destkeys == []:
            logger.debug("MAIN: _action_moveseed; now adding destination gkey: %s"
                % str(sourcekeys[0]))
            success = dest.add(sourcekeys[0])
            logger.debug("MAIN: _action_moveseed; success: %s" %str(success))
            logger.debug("MAIN: _action_moveseed; now deleting sourcekey: %s" % str(sourcekeys[0]))
            success = self.seeds.delete(sourcekeys[0])
            if success:
                success = dest.save()
                logger.debug("MAIN: _action_moveseed; destination saved... %s" %str(success))
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


    def _action_listkey(self, args):
        '''Action listskey method'''
        pass


    def _action_addkey(self, args):
        '''Action addkey method'''
        kwargs = self.build_gkeydict(args)
        logger.debug("MAIN: _action_listseed; kwargs: %s" % str(kwargs))
        self.seeds = self._load_seeds(args.seeds)
        if self.seeds:
            # get the desired seed
            keyresults = self.seeds.list(**kwargs)
            if keyresults and not args.nick == '*':
                self.output_results(keyresults, "\n Found GKEY seeds:")
            elif keyresults:
                self.output_results(['all'], "\n Installing seeds:")
            else:
                logger.info("MAIN: _action_addkey; "
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
            logger.debug("MAIN: _action_addkey; keysdir = %s" % keydir)
            self.gpg = GkeysGPG(self.config, keydir)
            results = {}
            failed = []
            for key in keyresults:
                if not key.keyid and not key.longkeyid and not args.nick == '*':
                    logger.debug("MAIN: _action_addkey; NO key id's to add... Ignoring")
                    return {"Failed: No keyid's found for %s" % key.name : ''}
                elif not key.keyid and not key.longkeyid:
                    print("No keyid's found for:", key.nick, key.name, "Skipping...")
                    failed.append(key)
                    continue
                logger.debug("MAIN: _action_addkey; adding key:")
                logger.debug("MAIN: " + str(key))
                results[key.name] = self.gpg.add_key(key)
                for result in results[key.name]:
                    logger.debug("MAIN: _action_addkey; result.failed = " +
                        str(result.failed))
                if self.print_results:
                    for result in results[key.name]:
                        print("key desired:", key.name, ", key added:",
                            result.username, ", succeeded:",
                            not result.failed, ", keyid:", result.keyid,
                            ", fingerprint:", result.fingerprint)
                        logger.debug("stderr_out: " + str(result.stderr_out))
                        if result.failed:
                            failed.append(key)
            if failed:
                self.output_results(failed, "\n Failed to install:")
            return {'Completed'}
        return {"No seeds to search or install": False}


    def _action_removekey(self, args):
        '''Action removekey method'''
        pass


    def _action_movekey(self, args):
        '''Action movekey method'''
        pass


    def user_confirm(self, message):
        '''Get input from the user to confirm to proceed
        with the desired action

        @param message: string, user promt message to display
        @return boolean: confirmation to proceed or abort
        '''
        pass


    def output_failed(self, failed):
        pass
