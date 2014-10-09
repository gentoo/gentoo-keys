#
#-*- coding:utf-8 -*-

'''Gentoo-keys - seed.py
This is gentoo-keys superclass which wraps the pyGPG lib
with gentoo-keys specific convienience functions.

 Distributed under the terms of the GNU General Public License v2

 Copyright:
             (c) 2011 Brian Dolbec
             Distributed under the terms of the GNU General Public License v2

 Author(s):
             Brian Dolbec <dolsen@gentoo.org>

'''

import json
import os

from gkeys.log import logger
from gkeys.config import GKEY
from gkeys.fileops import ensure_dirs


class Seeds(object):
    '''Handles all seed key file operations'''


    def __init__(self, filepath=None, config=None):
        '''Seeds class init function

        @param filepath: string of the file to load
        '''
        self.filename = filepath
        self.config = config
        self.seeds = {}


    def load(self, filename=None):
        '''Load the seed file into memory'''
        if filename:
            self.filename = filename
        if not self.filename:
            logger.debug("Seed: load; Not a valid filename: '%s'" % str(self.filename))
            return False
        logger.debug("Seeds: load; Begin loading seed file %s" % self.filename)
        seedlines = None
        self.seeds = {}
        try:
            with open(self.filename, "r+") as seedfile:
                seedlines = json.load(seedfile)
        except IOError as err:
            logger.debug("Seed: load; IOError occurred while loading file")
            self._error(err)
            return False
        for seed in seedlines.items():
            #try:
            self.seeds[seed[0]] = GKEY(**seed[1])
            #except Exception as err:
                #logger.debug("Seed: load; Error splitting seed: %s" % seed)
                #logger.debug("Seed: load; ...............parts: %s" % str(parts))
                #self._error(err)
        logger.debug("Seed: load; Completed loading seed file %s" % self.filename)
        return True


    def save(self, filename=None):
        '''Save the seeds to the file'''
        if filename:
            self.filename = filename
        if not self.filename:
            logger.debug("Seed: save; Not a valid filename: '%s'" % str(self.filename))
            return False
        logger.debug("Seed: save; Begin saving seed file %s" % self.filename)
        ensure_dirs(os.path.split(self.filename)[0],
            mode=int(self.config.get_key('permissions', "directories"),0),
            fatal=True)
        os.umask(int(self.config.get_key("permissions", "files"),0))
        try:
            with open(self.filename, 'w') as seedfile:
                seedfile.write(self._seeds2json(self.seeds))
                seedfile.write("\n")
        except IOError as err:
            self._error(err)
            return False
        return True


    def add(self, dev, gkey):
        '''Add a new seed key to memory'''
        if isinstance(gkey, dict) or isinstance(gkey, GKEY):
            self.seeds[dev] = gkey
            return True
        return False


    def delete(self, gkey=None):
        '''Delete the key from the seeds in memory

        @param gkey: GKEY, the matching GKEY to delete
        '''
        if gkey:
            try:
                self.seeds.pop(gkey.nick, None)
            except ValueError:
                return False
            return True


    def list(self, **kwargs):
        '''List the key or keys matching the kwargs argument or all

        @param kwargs: dict of GKEY._fields and values
        @returns list
        '''
        if not kwargs or kwargs['nick'] == '*':
            return self.seeds.values()
        # proceed with the search
        # discard any invalid keys
        keys = kwargs
        result = self.seeds
        for key in keys:
            if key in ['fingerprint']:
                result = {dev: gkey for dev, gkey in result.items() if kwargs[key] in getattr(gkey, key)}
            else:
                result = {dev: gkey for dev, gkey in result.items() if kwargs[key] == getattr(gkey, key)}
        return result.values()


    def search(self, pattern):
        '''Search for the keys matching the regular expression pattern'''
        pass


    def nick_search(self, nick):
        '''Searches the seeds for a matching nick

        @param nick: string
        @returns GKEY instance or None
        '''
        try:
            return self.seeds[nick]
        except KeyError:
            return None


    def _error(self, err):
        '''Class error logging function'''
        logger.error("Seed: Error processing seed file %s" % self.filename)
        logger.error("Seed: Error was: %s" % str(err))


    def _seeds2json(self, seeds):
        is_gkey = False
        if not seeds:
            seeds = {}
        elif isinstance(seeds.values()[0], GKEY):
            is_gkey = True
        for dev, value in seeds.items():
            if is_gkey:
                seeds[dev] = dict(value._asdict())
        return json.dumps(seeds, sort_keys=True, indent=4)


    def update(self, gkey):
        '''Looks for existance of a matching nick already in the seedfile
        if it exists. Then either adds or replaces the gkey
        @param gkey: GKEY instance
        '''
        oldkey = self.nick_search(gkey.nick)
        if oldkey:
            self.delete(oldkey)
        self.add(gkey.nick, gkey)
