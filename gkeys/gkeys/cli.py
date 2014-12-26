#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - cli.py

    Command line interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function


import sys

from gkeys.base import CliBase
from gkeys.actions import Actions, Available_Actions, Action_Options, Action_Map
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
            'Actions': Actions,
            'Available_Actions': Available_Actions,
            'Action_Options': Action_Options,
            'Action_Map': Action_Map,
            'prog': 'gkeys',
            'description': 'Gentoo-keys manager program',
            'epilog': '''CAUTION: adding UNTRUSTED keys can be HAZARDOUS to your system!'''
        }


    def __call__(self, args=None):
        """Main class call function

        @param args: Optional list of argumanets to parse and action to run
                     Defaults to sys.argv[1:]
        """
        if args:
            return self.run(self.parse_args(args))
        else:
            return self.run(self.parse_args(sys.argv[1:]))

