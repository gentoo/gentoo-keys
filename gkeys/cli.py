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

from gkeys.log import logger
from gkeys.config import GKeysConfig, GKEY
from gkeys.seed import Seeds


# set debug level to max
logger.setLevel(1)


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
        logger.debug('MAIN: parse_args; args: %s' % args)
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

        return parser.parse_args(args)


    def run(self, args):
        '''Run the args passed in

        @param args: list or argparse.Namespace object
        '''
        if not args:
            logger.error("Main: run; invalid args argument passed in")
        if isinstance(args, list):
            args = self.parse_args(args)
        if args.config:
            logger.debug("Main: run; Found alternate config request: %s" % args.config)
            self.config.defaults['config'] = args.config
        # now make it load the config file
        self.config.read_config()

        func = getattr(self, '_action_%s' % args.action)
        logger.debug('Main: run; Found action: %s' % args.action)
        results = func(args)
        if not results:
            print("No results found.  Check your configuration and that the",
                "seed file exists.")
            return
        # super simple output for the time being
        if self.print_results:
            print('\n\nGkey results:')
            print("\n".join([str(x) for x in results]))
            print()


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
        seeds = self._load_seeds(args.seeds)
        if seeds:
            results = seeds.list(**kwargs)
            return results
        return None


    def _action_addseed(self, args):
        '''Action addseed method'''
        parts = self.build_gkeylist(args)
        gkey = GKEY._make(parts)
        logger.debug("MAIN: _action_addseed; new gkey: %s" % str(gkey))
        seeds = self._load_seeds(args.seeds)
        gkeys = self._action_listseed(args)
        if len(gkeys) == 0:
            logger.debug("MAIN: _action_addkey; now adding gkey: %s" % str(gkey))
            success = seeds.add(gkey)
            if success:
                success = seeds.save()
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
        seeds = self._load_seeds(args.seeds)
        gkeys = self._action_listseed(args)
        if len(gkeys) == 1:
            logger.debug("MAIN: _action_removeseed; now deleting gkey: %s" % str(gkeys[0]))
            success = seeds.delete(gkeys[0])
            if success:
                success = seeds.save()
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
        seeds = self._load_seeds(args.seeds)
        kwargs = self.build_gkeydict(args)
        sourcekeys = seeds.list(**kwargs)
        dest = self._load_seeds(args.destination)
        destkeys = dest.list(**kwargs)
        messages = []
        if len(sourcekeys) == 1 and destkeys == []:
            logger.debug("MAIN: _action_moveseed; now adding destination gkey: %s"
                % str(sourcekeys[0]))
            success = dest.add(sourcekeys[0])
            logger.debug("MAIN: _action_moveseed; success: %s" %str(success))
            logger.debug("MAIN: _action_moveseed; now deleting sourcekey: %s" % str(sourcekeys[0]))
            success = seeds.delete(sourcekeys[0])
            if success:
                success = dest.save()
                logger.debug("MAIN: _action_moveseed; destination saved... %s" %str(success))
                success = seeds.save()
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
        pass


    def _action_removekey(self, args):
        '''Action removekey method'''
        pass


    def _action_movekey(self, args):
        '''Action movekey method'''
        pass






