#
#-*- coding:utf-8 -*-

from __future__ import print_function


import os
import sys

from gkeys import __version__
from gkeys.config import GKeysConfig
from gkeys.base import CliBase
from gkeygen.actions import Actions, Available_Actions, Action_Map


class Main(CliBase):
    '''Main command line interface class'''


    def __init__(self, root=None, config=None, print_results=True):
        """ Main class init function.

        @param root: string, root path to use
        @param config: optional GKeysConfig instance, For API use
        @param print_results: optional boolean, for API use
        """
        CliBase.__init__(self)
        self.root = root or "/"
        self.config = config or GKeysConfig(root=root)
        self.config.options['print_results'] = print_results
        self.cli_config = {
            'Actions': Actions,
            'Available_Actions': Available_Actions,
            'Action_Map': Action_Map,
            'Base_Options': [],
            'prog': 'gkeys-gen',
            'description': 'Gentoo Keys GPG key generator program',
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
            configs = [
                os.path.join(self.config['configdir'],'gkeys.conf'),
                os.path.join(self.config['configdir'],'gkeys-gen.conf'),
                ]
            ok = self.setup(args, configs)
        if ok:
            return self.run(args)
        return False
