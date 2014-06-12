#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - seedhandler.py

    Seed handling interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

import re

from gkeys.config import GKEY


class SeedHandler(object):

    def __init__(self, logger):
        self.logger = logger
        self.fingerprint_re = re.compile('[0-9A-Fa-f]{40}')
        self.finerprint_re2 = re.compile('[0-9A-Fa-f]{4}( [0-9A-Fa-f]{4}){9}')


    def new(self, args, checkgkey=False):
        newgkey = self.build_gkeydict(args)
        if checkgkey:
            newgkey = self.check_gkey(newgkey)
        if newgkey:
            newgkey = GKEY(**newgkey)
            self.logger.debug("SeedHandler: new() new gkey: %s" % str(newgkey))
        else:
            self.logger.debug("SeedHandler: new() FAILED to et parts from: %s"
                % str(args))
            return None
        return newgkey


    @staticmethod
    def build_gkeydict(args):
        keyinfo = {}
        for attr in GKEY._fields:
            try:
                value = getattr(args, attr)
                if value:
                    keyinfo[attr] = value
            except AttributeError:
                pass
        return keyinfo

    def check_gkey(self, args):
      # assume it's good until an error is found
      is_good = True
      try:
          if args['fingerprint']:
              # create a longkeyid based on fingerprint
              is_ok = self._check_fingerprint_integrity(args)
              args['keydir'] = args.get('keydir', args['nick'])
              if not is_ok:
                is_good = False
                self.logger.error('Bad fingerprint from command line args.')
      except KeyError:
          self.logger.error('GPG fingerprint not found.')
          is_good = False
      # need to add values to a list
      for key, value in args.items():
          args[key] = value.split()
      if is_good:
          return args
      else:
          self.logger.error('A valid fingerprint '
                  'was not found for %s' % args['name'])
      return args

    def _check_fingerprint_integrity(self, gkey):
        # assume it's good unti an error is found
        is_good = True
        fingerprint = gkey['fingerprint']
        # check fingerprint integrity
        if len(fingerprint) != 40:
            self.logger.error('  GPGKey incorrect fingerprint ' +
                    'length (%s) for fingerprint: %s' %(len(fingerprint), fingerprint))
            is_good = False
        if not self.fingerprint_re.match(fingerprint):
            self.logger.error('  GPGKey: Non hexadecimal digits in ' + 'fingerprint for fingerprint: ' + fingerprint)
            is_good = False
        return is_good
