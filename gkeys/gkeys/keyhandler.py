#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - keyhandler.py

    GKEY handling interface module

    @copyright: 2015 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""
import os
import sys

from snakeoil.demandload import demandload

if sys.version_info[0] >= 3:
    _unicode = str
else:
    _unicode = unicode

from  gkeys.gkey import GKEY


demandload(
    "gkeys.seedhandler:SeedHandler",
)

KEY_OPTIONS = ['nick', 'name', 'keydir', 'fingerprint', 'keyid', 'uid']


class KeyHandler(object):
    '''Class to hold various key operations'''


    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self._seedhandler = None


    @property
    def seedhandler(self):
        if not self._seedhandler:
            self._seedhandler = SeedHandler(self.logger, self.config)
        return self._seedhandler


    def autosearch_key(self, args, results):
        '''Search for the correct keyid from the GPGResult'''
        messages = []
        has_no_pubkey, s_keyid = results.no_pubkey
        if has_no_pubkey:
            messages.append(
                _unicode("Auto-searching for key.: 0x%s") % s_keyid)
            # reset all but keyid and pass thru data
            args.keyid = s_keyid
            args.keydir = None
            args.fingerprint = None
            args.exact = False
            args.category = None
            args.nick = None
            args.name = None
            args.all = False
            keys = self.key_search(args)
            if keys:
                args.category = list(keys)[0]
                args.nick = keys[args.category][0].nick
                return (True, args, messages)
            messages.append(_unicode("Failed to find gpg key.: 0x%s") % s_keyid)
        return (False, args, messages)


    def determine_keys(self, args, default_cat=None):
        seeds = self.seedhandler.load_category(args.category or default_cat)
        keyring = self.config.get_key('keyring')
        catdir = os.path.join(keyring, args.category)
        self.logger.debug(_unicode("KeyHandler: determine_keys; catdir = %s") % catdir)
        kwargs = self.seedhandler.build_gkeydict(args)
        return (catdir, seeds.list(**kwargs))


    def key_search(self, args, first_match=False):
        '''Search for a key's seed in the installed keys db'''
        results = {}
        search_args = [x for x in KEY_OPTIONS if getattr(args, x)]
        if args.category:
            self.seedhandler.load_category(args.category)
            results[args.category] = self.seedhandler.key_search(args, search_args)
        else:
            for cat in sorted(self.config.get_key('seeds')):
                self.seedhandler.load_category(cat)
                found = self.seedhandler.key_search(args, search_args)
                if found:
                    if cat in results:
                        results[cat].extend(found)
                    else:
                        results[cat] = found
                    if first_match:
                        break
        keys = {}
        for cat in results:
            keys[cat] = []
            for result in results[cat]:
                if result and result.nick not in keys[cat]:
                    if isinstance(result, GKEY):
                        keys[cat].append(result)

        self.logger.debug(_unicode("KeyHandler: key_search; keys = %s") % str(keys))
        return keys
