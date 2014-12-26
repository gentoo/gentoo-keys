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

if sys.version_info[0] >= 3:
    from urllib.request import urlopen
    py_input = input
    _unicode = str
else:
    from urllib2 import urlopen
    py_input = raw_input
    _unicode = unicode

from gkeys.fileops import ensure_dirs

Available_Actions = ["genkey"]

GPG_CONF = "https://api.gentoo.org/gentoo-keys/specs/glep63-gpg-conf.skel"
SPEC = "https://api.gentoo.org/gentoo-keys/specs/glep63.spec"

class Actions(object):

    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger

    def genkey(self, args):
        '''Key generation action'''
        if not args.homedir:
            gpghome = os.path.join(os.getcwd(), 'gpghome')
        else:
            if os.path.exists(args.homedir):
                gpghome = os.path.join(args.homedir, 'gpghome')
            else:
                self.output("Aborting... %s path does not exist." % args.homedir)
                return False
        self.logger.debug("MAIN: _action_genkey; setting gpghome destination: %s" % gpghome)
        self.logger.debug("MAIN: _action_genkey; args= %s" % str(args))
        key_params = self.get_input()
        ack = None
        while ack not in ["y", "yes", "n", "no"]:
            ack = py_input("Continue?[y/n]: ").lower()
        if ack in ["n", "no"]:
            self.output("\nKey generation aborted.")
            return False
        elif ack in ["y", "yes"]:
            # Set the environment to custom gpg directory
            os.environ['GNUPGHOME'] = gpghome
            gpghome_full_path = os.path.abspath(gpghome)
            self.logger.info("MAIN: _action_genkey; create custom gpg directory: %s" % gpghome_full_path)
            self.output("\n* Creating gpg folder at %s" % gpghome_full_path)
            ensure_dirs(gpghome)
            # Copy default gpg-conf.skel and append glep63 requirements
            self.output("* Creating gpg.conf file at %s" % gpghome_full_path)
            newgpgconfpath = os.path.join(gpghome, 'gpg.conf')
            shutil.copy('/usr/share/gnupg/gpg-conf.skel', newgpgconfpath)
            with open(newgpgconfpath, 'a') as conf:
                for line in urlopen(GPG_CONF):
                    conf.write(_unicode(line))
            # Key generation
            ctx = gpgme.Context()
            self.logger.info("MAIN: _action_genkey: Generating GPG key...")
            self.output("""
    ____________________
    < Generating GPG key >
     --------------------
            \   ^__^
             \  (oo)\_______
                (__)\       )\/
                    ||----w |
                    ||     ||""")
            self.output("\n* Give the password for the key. (Pick a strong one)\n")
            try:
                result = ctx.genkey(key_params)
            except gpgme.GpgmeError:
                self.logger.debug("MAIN: _action_genkey: Aborting... No given password.")
                self.output("Aborting... No given password.")
                return False
            key = ctx.get_key(result.fpr, True)
            self.logger.debug("MAIN: _action_genkey: Generated key: %s - %s"
                              % (key.uids[0].uid, key.subkeys[0].fpr))
            self.output("Your new GLEP 63 based OpenPGP key has been created in %s" % gpghome_full_path)
            self.output("""
        GPG key info:
            Full Name: %s,
            Email: %s,
            Fingerprint: %s
                        """ % (key.uids[0].name, key.uids[0].email,
                               key.subkeys[0].fpr))
            self.output("In order to use your new key, place the new gpghome to your ~/.gnupg folder by running the following command:\n"
                        "    mv %s ~/.gnupg\n"
                        "Important: If you have another old key in ~/.gnupg please make sure you backup it up first.\n\n"
                        "Please read the FAQ for post-generation steps that are available in: \n"
                        "https://wiki.gentoo.org/wiki/Project:Gentoo-keys/Generating_GLEP_63_based_OpenPGP_keys\n" % gpghome_full_path)
            return True

    def get_input(self):
        '''Interactive user input'''
        self.output("\nGPG key creator based on GLEP 63\n"
                    "(https://wiki.gentoo.org/wiki/GLEP:63)\n")
        name = py_input("Give your Full Name: ")
        email = py_input("Give your Email: ")
        while not re.match(r'[\w.-]+@[\w.-]+', email):
            self.output("\nBad email input. Try again.")
            email = py_input("Give your Email: ")
        print("\nReview:\n Full Name: %s\n Email: %s\n" % (name, email))
        key_properties = urlopen(SPEC).read()
        return _unicode(key_properties).format(name, email)
