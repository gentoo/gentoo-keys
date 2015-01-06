#
#-*- coding:utf-8 -*-

"""
    Gentoo-Keys - gkeygen/actions.py

    Primary API interface module
    @copyright: 2014 by Pavlos Ratis <dastergon@gentoo.org>
    @license: GNU GPL2, see COPYING for details
"""

import gpgme
import os
import re
import shutil
import sys

from collections import OrderedDict

if sys.version_info[0] >= 3:
    from urllib.request import urlopen
    py_input = input
    _unicode = str
else:
    from urllib2 import urlopen
    py_input = raw_input
    _unicode = unicode

from gkeys.fileops import ensure_dirs


Action_Map = OrderedDict({
    'gen-key': {
        'func': 'genkey',
        'options': ['spec', 'dest'],
        'desc': '''Generate a gpg key using a spec file''',
        'long_desc': '''Generate a gpg key using a spec file''',
        'example': '''''',
        },
    'list-specs': {
        'func': 'list_specs',
        'options': [],
        'desc': '''List spec file definitions (spec names) found in the config''',
        'long_desc': '''List spec file definitions (spec names) found in the config.
    The default-spec setting when the pkg was installed is set to glep-63-recommended.''',
        'example': '''$ gkey-gen list-specs

 Gkey task results:
    Specs defined: glep-63,  default-spec,  glep-63-recommended
''',
        },
})

Available_Actions = ['gen-key', 'list-specs']

LARRY = """
    ____________________
    < Generating GPG key >
     --------------------
            \   ^__^
             \  (oo)\_______
                (__)\       )\/
                    ||----w |
                    ||     ||"""

GPG_INFO_STRING = """
        GPG key info:
            Full Name: %s,
            Email: %s,
            Fingerprint: %s
                        """


class Actions(object):

    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger


    def genkey(self, args):
        '''Generate a gpg key using a spec file'''
        messages = []
        if not args.destination:
            gpghome = self.config.get_key('gkeys-gen', 'gpg-home')
        else:
            if os.path.exists(args.destination):
                gpghome = os.path.join(args.destination, 'gpghome')
            else:
                messages.extend(['', "Aborting... %s path does not exist." % args.destination])
                return (False, messages)
        self.logger.debug("MAIN: _action_genkey; setting gpghome destination: %s" % gpghome)
        self.logger.debug("MAIN: _action_genkey; args= %s" % str(args))
        if not args.spec:
            args.spec = self.config.get_key('spec', 'default-spec')
        key_params = self.get_input(args)
        ack = None
        while ack not in ["y", "yes", "n", "no"]:
            ack = py_input("Continue?[y/n]: ").lower()
        if ack in ["n", "no"]:
            messages.extend(['', "\nKey generation aborted."])
            return (False. messages)
        elif ack in ["y", "yes"]:
            # Set the environment to custom gpg directory
            os.environ['GNUPGHOME'] = gpghome
            gpghome_full_path = os.path.abspath(gpghome)
            self.logger.info("MAIN: _action_genkey; create custom gpg directory: %s" % gpghome_full_path)
            self.output(["\n* Creating gpg folder at %s" % gpghome_full_path])
            ensure_dirs(gpghome)
            # Copy default gpg-conf.skel and append glep63 requirements
            self.output(["* Creating gpg.conf file at %s" % gpghome_full_path])
            newgpgconfpath = os.path.join(gpghome, 'gpg.conf')
            shutil.copy('/usr/share/gnupg/gpg-conf.skel', newgpgconfpath)
            with open(newgpgconfpath, 'a') as conf:
                for line in urlopen(self.config.get_key('gpg-urls', args.spec)):
                    conf.write(_unicode(line.decode('utf-8')))
            # Key generation
            ctx = gpgme.Context()
            self.logger.info("MAIN: _action_genkey: Generating GPG key...")
            self.output([LARRY])
            self.output(["* Give the password for the key. (Pick a strong one)",
                "    Please surf the internet, type on your keyboard, etc. ",
                "    This helps the random number generator work effectively"])
            try:
                result = ctx.genkey(key_params)
            except gpgme.GpgmeError as e:
                self.logger.debug("MAIN: _action_genkey: GpgmeError: %s" % str(e))
                self.logger.debug("MAIN: _action_genkey: Aborting... Failed to get a password.")
                messages.extend(['', "Aborting... Failed to get a password."])
                return (False, messages)
            key = ctx.get_key(result.fpr, True)
            self.logger.debug("MAIN: _action_genkey: Generated key: %s - %s"
                              % (key.uids[0].uid, key.subkeys[0].fpr))
            self.output(["Your new GLEP 63 based OpenPGP key has been created in %s" % gpghome_full_path])
            self.output([GPG_INFO_STRING % (key.uids[0].name, key.uids[0].email,
                               key.subkeys[0].fpr)])
            self.output(["In order to use your new key, place the new gpghome to your ~/.gnupg folder by running the following command:",
                        "    mv %s ~/.gnupg" % gpghome_full_path,
                        "Important: If you have another old key in ~/.gnupg please make sure you backup it up first.\n",
                        "Please read the FAQ for post-generation steps that are available in:",
                        "https://wiki.gentoo.org/wiki/Project:Gentoo-keys/Generating_GLEP_63_based_OpenPGP_keys"])
            return (True, messages)


    def get_input(self, args):
        '''Interactive user input'''
        self.output(['', "GPG key creator",
            "    Spec file..: %s" % args.spec,
            "    Homepage...: %s"
            % self.config.get_key('spec-homepage', args.spec),
            ])
        name = py_input("Give your Full Name: ")
        email = py_input("Give your Email: ")
        while not re.match(r'[\w.-]+@[\w.-]+', email):
            self.output(["\nBad email input. Try again."])
            email = py_input("Give your Email: ")
        print("\nReview:\n Full Name: %s\n Email: %s\n" % (name, email))
        url = self.config.get_key('spec-urls', args.spec)
        key_properties = urlopen(url).read()
        return _unicode(key_properties.decode('utf-8')).format(name, email)


    def list_specs(self, args):
        '''List seed file definitions found in the config'''
        specs = list(self.config.get_key('spec'))
        return (True, {"Specs defined: %s\n"
            % (",  ".join(specs)): True})


