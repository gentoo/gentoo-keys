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

from gkeys import config, fileops, seed, lib
from gkeys.actions import Actions, Available_Actions
from gkeys.config import GKeysConfig
from gkeys.log import log_levels, set_logger



class Main(object):
    '''Main command line interface class'''


    def __init__(self, root=None, config=None, print_results=True):
        """ Main class init function.

        @param root: string, root path to use
        """
        self.root = root or "/"
        self.config = config or GKeysConfig(root=root)
        self.config.options['print_results'] = print_results
        self.args = None
        self.seeds = None
        self.actions = None


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
        parser = argparse.ArgumentParser(
            prog='gkeys',
            description='Gentoo-keys manager program',
            epilog='''Caution: adding untrusted keys to these keyrings can
                be hazardous to your system!''')

        # options
        parser.add_argument('-c', '--config', dest='config', default=None,
            help='The path to an alternate config file')
        parser.add_argument('-d', '--dest', dest='destination', default=None,
            help='The destination seed file or keydir for move, copy operations')
        parser.add_argument('-D', '--debug', default='DEBUG',
            choices=list(log_levels),
            help='The logging level to set for the logfile')
        parser.add_argument('-f', '--fingerprint', dest='fingerprint', default=None,
            help='The fingerprint of the the key')
        parser.add_argument('-k', '--keyring', dest='keyring', default='trusted_keyring',
            help='The name of the keyring to use')
        parser.add_argument('-n', '--nick', dest='nick', default=None,
            help='The nick associated with the the key')
        parser.add_argument('-N', '--name', dest='name', nargs='*',
            default=None, help='The name of the the key')
        parser.add_argument('-r', '--keydir',
            choices=['rel', 'dev', 'overlays'], dest='keydir', default=None,
            help='The keydir to use or update')
        parser.add_argument('-s', '--seeds',
            choices=['rel', 'dev'], dest='seeds', default=None,
            help='The seeds file to use or update')
        parser.add_argument('-S', '--seedfile', dest='seedfile', default=None,
            help='The seedfile path to use')
        parser.add_argument('-F', '--file', dest='filename', default=None,
               help='The path/URL to use for the signed file')
        parser.add_argument('-z','--signature', dest='signature', default=None,
           help='The path/URL to use for the signature')


        subparsers = parser.add_subparsers(help='actions')
        for name in Available_Actions:
            action_method = getattr(Actions, name)
            actiondoc = action_method.__doc__
            try:
                text = actiondoc.splitlines()[0]
            except AttributeError:
                text = ""
            action_parser = subparsers.add_parser(
                name,
                help=text,
                description=actiondoc,
                formatter_class=argparse.RawDescriptionHelpFormatter)
            action_parser.set_defaults(action=name)

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
        logger = set_logger('gkeys', self.config['logdir'], args.debug,
            dirmode=int(self.config.get_key('permissions', 'directories'),0),
            filemask=int(self.config.get_key('permissions', 'files'),0))
        config.logger = logger
        fileops.logger = logger
        seed.logger = logger
        lib.logger = logger

        if message:
            logger.error(message)

        # now that we have a logger, record the alternate config setting
        if args.config:
            logger.debug("Main: run; Found alternate config request: %s"
                % args.config)

        # establish our actions instance
        self.actions = Actions(self.config, self.output_results, logger)

        # run the action
        func = getattr(self.actions, '%s' % args.action)
        logger.debug('Main: run; Found action: %s' % args.action)
        results = func(args)
        if not results:
            print("No results found.  Check your configuration and that the",
                "seed file exists.")
            return
        if self.config.options['print_results'] and 'done' not in list(results):
            self.output_results(results, '\n Gkey task results:')
            print()


    @staticmethod
    def output_results(results, header):
        # super simple output for the time being
        print(header)
        for msg in results:
            if isinstance(msg, str):
                print(msg)
            else:
                try:
                    print("\n".join([x.pretty_print for x in msg]))
                except AttributeError:
                    for x in msg:
                        print(x)
        print()


    def output_failed(self, failed):
        pass
