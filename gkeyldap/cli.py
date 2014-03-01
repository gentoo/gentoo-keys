#
#-*- coding:utf-8 -*-

from __future__ import print_function


import sys
import argparse

from gkeys import log
from gkeys.log import log_levels, set_logger

from gkeys import config
from gkeys import seed

from gkeys.config import GKeysConfig
from gkeyldap import search
from gkeyldap.actions import Actions, Available_Actions
logger = log.logger


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
        actions = Available_Actions
        parser = argparse.ArgumentParser(
            prog='gkeys',
            description='Gentoo-keys manager program',
            epilog='''Caution: adding untrusted keys to these keyrings can
                be hazardous to your system!''')
        # actions
        parser.add_argument('action', choices=actions, nargs='?',
            default='ldapsearch', help='Search ldap or update the seed file')
        # options
        parser.add_argument('-c', '--config', dest='config', default=None,
            help='The path to an alternate config file')
        parser.add_argument('-d', '--dest', dest='destination', default=None,
            help='The destination db file path')
        parser.add_argument('-N', '--name', dest='name', default=None,
            help='The name to search for')
        parser.add_argument('-n', '--nick', dest='nick', default=None,
            help='The nick or user id (uid) to search for')
        parser.add_argument('-m', '--mail', dest='mail', default=None,
            help='The email address to search for')
        parser.add_argument('-k', '--keyid', dest='keyid', default=None,
            help='The gpg keyid to search for')
        parser.add_argument('-f', '--fingerprint', dest='fingerprint', default=None,
            help='The gpg fingerprint to search for')
        parser.add_argument('-S', '--status', default=False,
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
        logger = set_logger('gkeyldap', self.config['logdir'], args.debug)
        config.logger = logger
        seed.logger = logger
        search.logger = logger

        if message:
            logger.error(message)

        # now that we have a logger, record the alternate config setting
        if args.config:
            logger.debug("Main: run; Found alternate config request: %s"
                % args.config)

        # establish our actions instance
        self.actions = Actions(self.config, print, logger)

        logger.info("Begin running action: %s" % args.action)

        # run the action
        func = getattr(self.actions, '%s' % args.action)

        logger.debug('Main: run; Found action: %s' % args.action)
        results = func(args)
        return results


