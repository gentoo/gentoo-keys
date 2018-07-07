#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - base.py

    Command line interface argsparse options module
    and common functions

    @copyright: 2012-2015 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

from __future__ import print_function


import argparse
import os
import sys

from gkeys.fileops import ensure_dirs
from gkeys.log import log_levels, set_logger


if sys.version_info[0] >= 3:
    unicode = str


class Args(object):
    '''Basic argsparser replacement for using gkeys Actions via an API

    Holds the full spectrum of possible options supported.
    Not all options used by all actions.'''


    def __init__(self):
        self.action = None
        self.all = False
        self.category = None
        self.cleankey = False
        self.destination = None
        self.exact = False
        self.filename = None
        self.fingerprint = None
        self.keyid = None
        self.keyring = None
        self.keys = None
        self.nick = None
        self.name = None
        self.keydir = None
        self.seedfile = None
        self.signature = None
        self.status = False
        self.timestamp = None
        self.uid = None


class CliBase(object):
    '''Common cli and argsparse options class'''


    def __init__(self):
        self.cli_config = {
            'Actions': None,
            'Available_Actions': [],
            'Action_Map': {},
            'Base_Options': [],
            'prog': 'gkeys',
            'description': 'Gentoo-keys manager program',
            'epilog': '''Caution: adding UNTRUSTED keys can be HAZARDOUS to your system!'''
        }
        self.config = None
        self.args = None
        self.seeds = None
        self.actions = None
        self.logger = None
        self.version = None
        self.need_Action = True


    @staticmethod
    def _option_status(parser=None):
        parser.add_argument('-A', '--status', action='store_true',
            default=False,
            help='The active status of the member')

    @staticmethod
    def _option_all(parser=None):
        parser.add_argument('-a', '--all', dest='all',
            action='store_true', default=False,
            help='Match all inputs arguments in searches')

    @staticmethod
    def _option_category(parser=None):
        parser.add_argument('-C', '--category',
            dest='category', default=None,
            help='The key or seed directory category to use or update')

    @staticmethod
    def _option_cleankey(parser=None):
        parser.add_argument('--clean-key',
            dest='cleankey', default=False,
            help='Clean the key from the keyring due to failures')

    @staticmethod
    def _option_cleanseed(parser=None):
        parser.add_argument('--clean-seed',
            dest='cleanseed', default=False,
            help='Clean the seed from the seedfile due to failures.  '
                'Used during binary keyring release creation.')

    @staticmethod
    def _option_dest(parser=None):
        parser.add_argument('-d', '--dest', dest='destination', default=None,
            help='The destination for move, copy, create operations')

    @staticmethod
    def _option_exact(parser=None):
        parser.add_argument('-e', '--exact', dest='exact',
            action='store_true', default=False,
            help='Use CASE matching in searches')

    @staticmethod
    def _option_file(parser=None):
        parser.add_argument('-F', '--file', dest='filename', default=None,
            nargs='+',
            help='The path/URL to use for the (signed) file')

    @staticmethod
    def _option_1file(parser=None):
        parser.add_argument('-F', '--file', dest='filename', default=None,
            help='The path/URL to use for the (signed) file')

    @staticmethod
    def _option_fingerprint(parser=None):
        parser.add_argument('-f', '--fingerprint', dest='fingerprint',
            default=None, nargs='+',
            help='The fingerprint(s) of the the key or subkey')

    @staticmethod
    def _option_gpgsearch(parser=None):
        parser.add_argument('-g', '--gpgsearch', dest='gpgsearch',
            action='store_true', default=False,
            help='Do a gpg search operation, rather than a gkey search')

    @staticmethod
    def _option_homedir(parser=None):
        parser.add_argument('-H', '--homedir', dest='homedir', default=None,
                            help='The destination for the generated key')

    @staticmethod
    def _option_keyid(parser=None):
        parser.add_argument('-i', '--keyid', dest='keyid', default=None,
            nargs='+',
            help='The long keyid of the gpg key to search for')

    @staticmethod
    def _option_justdoit(parser=None):
        parser.add_argument('--justdoit', dest='justdoit',
            action='store_true', default=False,
            help='Just Do It')

    @staticmethod
    def _option_keyring(parser=None):
        parser.add_argument('-k', '--keyring', dest='keyring', default=None,
            help='The name of the keyring to use for verification, etc.')

    @staticmethod
    def _option_keys(parser=None):
        parser.add_argument('-K', '--keys', dest='keys', nargs='*',
            default=None,
            help='The fingerprint(s) of the primary keys in the keyring.')

    @staticmethod
    def _option_mail(parser=None):
        parser.add_argument('-m', '--mail', dest='mail', default=None,
            help='The email address to search for or use.')

    @staticmethod
    def _option_nick(parser=None):
        parser.add_argument('-n', '--nick', dest='nick', default=None,
            help='The nick associated with the the key')

    @staticmethod
    def _option_name(parser=None):
        parser.add_argument('-N', '--name', dest='name', nargs='*',
            default=None, help='The name of the the key')

    @staticmethod
    def _option_1name(parser=None):
        parser.add_argument('-N', '--name', dest='name',
            default=None, help='The name of the the key')

    @staticmethod
    def _option_keydir(parser=None):
        parser.add_argument('-r', '--keydir', dest='keydir', default=None,
            help='The keydir to use, update or search for/in')

    @staticmethod
    def _option_seedfile(parser=None):
        parser.add_argument('-S', '--seedfile', dest='seedfile', default=None,
            help='The seedfile to use from the gkeys.conf file')

    @staticmethod
    def _option_signature(parser=None):
        parser.add_argument('-s','--signature', dest='signature', default=None,
           help='The path/URL to use for the signature')

    @staticmethod
    def _option_spec(parser=None):
        parser.add_argument('-S', '--spec', dest='spec', default=None,
            help='The spec file to use from the gkeys-gen.conf file')

    @staticmethod
    def _option_timestamp(parser=None):
        parser.add_argument('-t', '--timestamp', dest='timestamp',
            action='store_true', default=False,
            help='Turn on timestamp use')

    @staticmethod
    def _option_uid(parser=None):
        parser.add_argument('-u', '--uid', dest='uid', nargs='+', default=None,
            help='The user ID, gpg key uid')


    def parse_args(self, argv):
        '''Parse a list of aruments

        @param argv: list
        @returns argparse.Namespace object
        '''
        #self.logger.debug('CliBase: parse_args; args: %s' % args)
        parser = argparse.ArgumentParser(
            prog=self.cli_config['prog'],
            description=self.cli_config['description'],
            epilog=self.cli_config['epilog'])

        # options
        parser.add_argument('-c', '--config', dest='config', default=None,
            help='The path to an alternate config file')
        parser.add_argument('-D', '--debug', default='DEBUG',
            choices=list(log_levels),
            help='The logging level to set for the logfile')
        parser.add_argument('-V', '--version', action = 'version',
                          version = self.version)

        # Add any additional options to the command base
        self._add_options(parser, self.cli_config['Base_Options'])

        if self.cli_config['Available_Actions']:
            subparsers = parser.add_subparsers(
                title='Subcommands',
                description='Valid subcommands',
                help='Additional help')
            for name in self.cli_config['Available_Actions']:
                actiondoc = self.cli_config['Action_Map'][name]['desc']
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
                options = self.cli_config['Action_Map'][name]['options']
                self._add_options(action_parser, options)

        parsed_args = parser.parse_args(argv)
        action = getattr(parsed_args, 'action', None)
        if self.need_Action and not action:
            parser.print_usage()
            sys.exit(1)
        elif action in ['---general---', '----keys-----', '----seeds----']:
            parser.print_help()
            sys.exit(1)
        return parsed_args


    def _add_options(self, parser, options):
        for opt in options:
            getattr(self, '_option_%s' % opt)(parser)


    def setup(self, args, configs):
        '''Set up the args and configs passed in

        @param args: list or argparse.Namespace object
        @param configs: list
        '''
        message = None
        if not args:
            message = "Main: run; invalid args argument passed in"
        if isinstance(args, list):
            args = self.parse_args(args)
        if args.config:
            self.config.defaults['config'] = args.config
            self.config.defaults['configdir'] = os.path.dirname(args.config)
            if args.email:
                configs = [self.config.defaults['config'], os.path.abspath(os.path.join(self.config.defaults['configdir'], "email.conf"))]
                self.config.read_config(configs)
            else:
                self.config.read_config()
        else:
            self.config.read_config(configs)

        # check for permissions and adjust configs accordngly
        if not self.config.defaults['homedir']:
            self.config.defaults['homedir'] = os.path.expanduser('~')
        if not os.access(self.config['logdir'], os.W_OK):
            self.config.options['logdir'] = os.path.join(self.config['userconfigdir'], 'logs')
            ensure_dirs(self.config.options['logdir'])
        # establish our logger and update it in the imported files
        self.logger = set_logger(self.cli_config['prog'], self.config['logdir'], args.debug,
            dirmode=int(self.config.get_key('permissions', 'directories'),0),
            filemask=int(self.config.get_key('permissions', 'files'),0))
        self.config.logger = self.logger

        if message:
            self.logger.error(message)

        # now that we have a logger, record the alternate config setting
        if args.config:
            self.logger.debug("Main: run; Found alternate config request: %s"
                % args.config)
        self.logger.debug("Main: run; Using config: %s" % self.config['config'])

        # check if a -C, --category was input
        # if it was, check if the category is listed in the [seeds]
        cat = None
        if 'category' in args:
            cat = args.category
        if not self._check_category(cat):
            return False
        return True


    def run(self, args):
        '''Run the action selected

        @param args: list of argumanets to parse
        '''
        # establish our actions instance
        self.actions = self.cli_config['Actions'](self.config, self.output_results, self.logger)

        # run the action
        func = getattr(self.actions, '%s'
            % self.cli_config['Action_Map'][args.action]['func'])
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
    def output_results(results, header=None):
        # super simple output for the time being
        if header:
            print(header)
        for msg in results:
            if type(msg) in [str, unicode]:
                print('   ', msg)
            else:
                try:
                    print(unicode("\n").join([x.pretty_print for x in msg]))
                except AttributeError:
                    for x in msg:
                        print('    ', x)
        print()


    def output_failed(self, failed):
        pass


    def _check_category(self, category=None):
        '''Checks that the category (seedfile) is listed
        in the [seeds] config or defaults['seeds'] section

        @param args: configparser instance
        @return boolean
        '''
        available_cats = list(self.config.defaults['seeds'])
        if category and category not in available_cats:
            self.logger.error("Invalid category or seedfile entered: %s" % category)
            self.logger.error("Available categories or seedfiles: %s" % ', '.join(sorted(available_cats)))
            return False
        return True
