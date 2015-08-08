#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - cli.py

    Command line interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function


import os
import sys

from gkeys import __version__
from gkeys.base import CliBase
from gkeys.config import GKeysConfig
from gkeys.keyhandler import KEY_OPTIONS
from gkeysgpg.actions import Actions, Available_Actions, Action_Map


class Main(CliBase):
    '''Main command line interface class'''


    def __init__(self, root=None, config=None, print_results=True):
        """ Main class init function.

        @param root: string, root path to use
        """
        CliBase.__init__(self)
        self.root = root or "/"
        self.config = config or GKeysConfig(root=root)
        self.config.options['print_results'] = print_results
        self.cli_config = {
            'Actions':  Actions,
            'Available_Actions': Available_Actions,
            'Action_Map': Action_Map,
            'Base_Options': Available_Actions.copy(),
            'prog': 'gkeys-gpg',
            'description': 'Gentoo-keys gpg command wrapper',
            'epilog': '''CAUTION: adding UNTRUSTED keys can be HAZARDOUS to your system!'''
        }
        self.cli_config['Base_Options'].extend(["dash", "statusfd"])
        self.cli_config['Base_Options'].extend(KEY_OPTIONS)
        self.cli_config['Base_Options'].extend(["category"])
        self.version = __version__
        self.need_Action = False


    def __call__(self, args=None):
        """Main class call function

        @param args: Optional list of argumanets to parse and action to run
                     Defaults to sys.argv[1:]
        """
        if args:
            ok = self.setup(args, [])
        else:
            args = self.parse_args(sys.argv[1:])
            ok = self.setup(args, os.path.join(self.config['configdir'],'gkeys.conf'))
        if ok:
            return self.run(args)
        return 1


    def run(self, args):
        '''Run the gpg command option

        @param args: list of argumanets to parse
        '''
        # establish our actions instance
        self.actions = self.cli_config['Actions'](self.config, self.output_results, self.logger)

        for action in self.cli_config['Available_Actions']:
            if getattr(args, action):
                break

        # run the action
        func = getattr(self.actions, '%s'
            % self.cli_config['Action_Map'][action]['func'])
        self.logger.debug('Main: run; Found action: %s' % action)
        returncode, results = func(args, sys.argv[1:])
        if not results:
            print("No results found.  Check your configuration and that the",
                "seed file exists.")
            return 1
        self.logger.debug("gpg results output:")
        self.logger.debug(results)
        self.logger.debug("Return code: %s, %s" %(str(returncode), type(returncode)))
        return returncode


    @staticmethod
    def _option_blank(parser=None):
        parser.add_argument('-', '--', dest='blank', nargs='', default=None,
            help='fill me in')

    @staticmethod
    def _option_clearsign(parser=None):
        parser.add_argument('--clearsign', dest='clearsign', default=None,
            help='make a clear text signature')

    @staticmethod
    def _option_detachsign(parser=None):
        parser.add_argument('-b', '--detach-sign', dest='detachsign', default=None,
            help='make a detached signature')

    @staticmethod
    def _option_sign(parser=None):
        parser.add_argument('-s', '--sign', dest='sign', default=None,
            help='make a signature')

    @staticmethod
    def _option_verify(parser=None):
        parser.add_argument('--verify', dest='verify', default=None,
            help='verify a signature')

### These are for gpg command compatibilty only
    @staticmethod
    def _option_statusfd(parser=None):
        parser.add_argument('--status-fd', dest='statusfd', default=None,
            help='Write special status strings to the file descriptor n.')

    @staticmethod
    def _option_dash(parser=None):
        parser.add_argument('-', dest='dash', action='store_true', default=False,
            help='read input from stdin.')


    def output_results(self, args, results):
        print(results[1].encode('utf-8'), file=sys.stderr)
        if args.statusfd == '1':
            print(results[0].encode('utf-8'))
        elif args.statusfd == '2':
            print(results, file=sys.stderr)
