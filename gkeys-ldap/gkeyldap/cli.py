#
#-*- coding:utf-8 -*-

from __future__ import print_function


import sys

from gkeys import config
from gkeys import seed

from gkeys.base import CliBase
from gkeys.config import GKeysConfig
from gkeyldap import connect, search
from gkeyldap.actions import Actions, Available_Actions


class Main(CliBase):
    '''Main command line interface class'''


    def __init__(self, root=None, config=None, print_results=True):
        """ Main class init function.

        @param root: string, root path to use
        @param config: optional GKeysConfig instance, For API use
        @param print_results: optional boolean, for API use
        """
        self.root = root or "/"
        self.config = config or GKeysConfig(root=root)
        self.print_results = print_results
        self.args = None
        self.seeds = None
        self.cli_config = {
            'Actions': Actions,
            'Available_Actions': Available_Actions,
            'Action_Options': Action_Options,
            'prog': 'gkey-ldap',
            'description': 'Gentoo-keys LDAP interface and seed file generator program',
            'epilog': '''Caution: adding untrusted keys to these keyrings can
                be hazardous to your system!'''
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

