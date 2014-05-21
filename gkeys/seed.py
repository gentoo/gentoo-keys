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

from collections import defaultdict
from gkeys.log import logger
from gkeys.config import GKEY


class Seeds(object):
    '''Handles all seed key file operations'''


    def __init__(self, filepath=None):
        '''Seeds class init function

        @param filepath: string of the file to load
        '''
        self.filename = filepath
        self.seeds = []


    def load(self, filename=None):
        '''Load the seed file into memory'''
        if filename:
            self.filename = filename
        if not self.filename:
            logger.debug("Seed: load; Not a valid filename: '%s'" % str(self.filename))
            return False
        logger.debug("Seeds: load; Begin loading seed file %s" % self.filename)
        seedlines = None
        self.seeds = []
        try:
            with open(self.filename) as seedfile:
                seedlines = json.load(seedfile)
        except IOError as err:
            logger.debug("Seed: load; IOError occurred while loading file")
            self._error(err)
            return False
        # initialize a dummy instance, so it can make new ones
        gkey = GKEY._make([None,None,None,None,None,None])
        for seed in seedlines.items():
            #try:
            self.seeds.append(gkey.make_packed_dict(seed[1]))
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
        try:
            with open(self.filename, 'w') as seedfile:
                seedfile.write(self._seeds2json(self.seeds))
                seedfile.write("\n")
        except IOError as err:
            self._error(err)
            return False
        return True


    def add(self, gkey):
        '''Add a new seed key to memory'''
        if isinstance(gkey, defaultdict):
            self.seeds.append(gkey)
            return True
        elif isinstance(gkey, GKEY):
            pass
        return False


    def delete(self, gkey=None, index=None):
        '''Delete the key from the seeds in memory

        @param gkey: GKEY, the matching GKEY to delete
        @param index: int, '''
        if gkey:
            try:
                self.seeds.remove(gkey)
            except ValueError:
                return False
            return True
        elif index:
            self.seeds.pop(index)
            return True


    def list(self, **kwargs):
        '''List the key or keys matching the kwargs argument or all

        @param kwargs: dict of GKEY._fields and values
        @returns list
        '''
        if not kwargs:
            return self.seeds
        if kwargs['nick'] == '*':
            return self.seeds[:]
        # proceed with the search
        # discard any invalid keys
        keys = set(list(kwargs)).intersection(GKEY._fields)
        result = self.seeds[:]
        for key in keys:
            result = [x for x in result if getattr(x , key) == kwargs[key]]
        return result


    def search(self, pattern):
        '''Search for the keys matching the regular expression pattern'''
        pass


    def index(self, gkey):
        '''The index of the gkey in the seeds list

        @param gkey: GKEY, the matching GKEY to delete
        @return int
        '''
        try:
            index = self.seeds.index(gkey)
        except ValueError:
            return None
        return index


    def _error(self, err):
        '''Class error logging function'''
        logger.error("Seed: Error processing seed file %s" % self.filename)
        logger.error("Seed: Error was: %s" % str(err))


    def _seeds2json(self, seeds):
        return json.dumps(self.seeds[0], sort_keys=True, indent=4)
