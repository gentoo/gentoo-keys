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
from gkeys.actions import Actions
from gkeys.action_map import Available_Actions, Action_Map
from gkeys.config import GKeysConfig



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
            'Actions': [],
            'Available_Actions': [],
            'Action_Map': [],
            'Base_Options': ['sign', 'verify'],
            'prog': 'gkeys-gpg',
            'description': 'Gentoo-keys gpg command wrapper',
            'epilog': '''CAUTION: adding UNTRUSTED keys can be HAZARDOUS to your system!'''
        }
        self.version = __version__


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
        return False

    def run(self, args):
        '''Run the gpg command option

        @param args: list of argumanets to parse
        '''
        self.logger.debug('Main: run; Found action: %s' % args.action)
        success, results = func(args)
        if not results:
            print("No results found.  Check your configuration and that the",
                "seed file exists.")
            return success
        if self.config.options['print_results'] and 'done' not in list(results):
            self.output_results(results, '\n Gkey task results:')
        return success


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




