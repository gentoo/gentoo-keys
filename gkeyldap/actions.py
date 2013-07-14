#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - gkeyldap/actions.py

    Primary api interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

import os

from gkeys.config import GKEY
from gkeys.seed import Seeds
from gkeyldap.search import (LdapSearch, UID, gkey2ldap_map, gkey2SEARCH)


# set some defaults
KEY_LEN = {
    'keyid': 8,
    'longkeyid': 16,
}


Avialable_Actions = ['ldapsearch', 'updateseeds']


def get_key_ids(key, info):
    '''Small utility function to return only keyid (short)
    or longkeyid's

    @param key: string, the key length desired
    @param info: list of keysid's to process
    @return list of the desired key length id's
    '''
    result = []
    for x in info:
        if x.startswith('0x'):
            mylen = KEY_LEN[key] + 2
        else:
            mylen = KEY_LEN[key]
        if len(x) == mylen:
            result.append(x)
    return result


class Actions(object):


    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger
        self.seeds = None


    def ldapsearch(self, args):
        l = LdapSearch()
        self.logger.info("Search...establishing connection")
        self.output("Search...establishing connection")
        if not l.connect():
            self.logger.info("Aborting Search...Connection failed")
            self.output("Aborting Search...Connection failed")
            return False
        self.logger.debug("MAIN: _action_ldapsearch; args = %s" % str(args))
        x, target, search_field = self.get_args(args)
        results = l.search(target, search_field)
        devs = l.result2dict(results, gkey2ldap_map[x])
        for dev in sorted(devs):
            self.output(dev, devs[dev])
        self.output("============================================")
        self.output("Total number of devs in results:", len(devs))
        return True


    def updateseeds(self, args):
        self.logger.info("Beginning ldap search...")
        self.output("Beginning ldap search...")
        l = LdapSearch()
        if not l.connect():
            self.output("Aborting Update...Connection failed")
            return False
        results = l.search('*', UID)
        info = l.result2dict(results, 'uid')
        self.logger.debug(
            "MAIN: _action_updateseeds; got results :) converted to info")
        if not self.create_seedfile(info):
            self.logger.error("Dev seed file update failure: "
                "Original seed file is intact & untouched.")
        old = self.config['dev-seedfile'] + '.old'
        try:
            self.output("Backing up existing file...")
            if os.path.exists(old):
                self.logger.debug(
                    "MAIN: _action_updateseeds; Removing 'old' seed file: %s"
                    % old)
                os.unlink(old)
            if os.path.exists(self.config['dev-seedfile']):
                self.logger.debug(
                    "MAIN: _action_updateseeds; Renaming current seed file to: "
                    "%s" % old)
                os.rename(self.config['dev-seedfile'], old)
            self.logger.debug(
                "MAIN: _action_updateseeds; Renaming '.new' seed file to: %s"
                % self.config['dev-seedfile'])
            os.rename(self.config['dev-seedfile'] + '.new',
                self.config['dev-seedfile'])
        except IOError:
            raise
        self.output("Developer Seed file updated")
        return True


    def create_seedfile(self, devs):
        self.output("Creating seeds from ldap data...")
        filename = self.config['dev-seedfile'] + '.new'
        self.seeds = Seeds(filename)
        count = 0
        for dev in sorted(devs):
            if devs[dev]['gentooStatus'][0] not in ['active']:
                continue
            #self.logger.debug("create_seedfile, dev = "
            #   "%s, %s" % (str(dev), str(devs[dev])))
            new_gkey = GKEY._make(self.build_gkeylist(devs[dev]))
            self.seeds.add(new_gkey)
            count += 1
        self.output("Total number of seeds created:", count)
        self.output("Seeds created...saving file: %s" % filename)
        return self.seeds.save()


    @staticmethod
    def get_args(args):
        for x in ['nick', 'name', 'gpgkey', 'fingerprint', 'status']:
            if x:
                target = getattr(args, x)
                search_field = gkey2SEARCH[x]
                break
        return (x, target, search_field)



    def build_gkeydict(self, info):
        keyinfo = {}
        for x in GKEY._fields:
            field = gkey2ldap_map[x]
            if not field:
                continue
            try:
                # strip errant line feeds
                values = [y.strip('\n') for y in info[field]]
                if values and values in ['uid', 'cn' ]:
                    value = values[0]
                # separate out short/long key id's
                elif values and x in ['keyid', 'longkeyid']:
                    value = get_key_ids(x, values)
                else:
                    value = values
                if 'undefined' in values:
                    self.logger.error('%s = "undefined" for %s, %s'
                        %(field, info['uid'][0], info['cn'][0]))
                if value:
                    keyinfo[x] = value
            except KeyError:
                pass
        return keyinfo


    def build_gkeylist(self, info):
        keyinfo = []
        keyid_found = False
        keyid_missing = False
        #self.logger.debug("MAIN: build_gkeylist; info = %s" % str(info))
        for x in GKEY._fields:
            field = gkey2ldap_map[x]
            if not field:
                keyinfo.append(None)
                continue
            try:
                # strip errant line feeds
                values = [y.strip('\n') for y in info[field]]
                if values and field in ['uid', 'cn' ]:
                    value = values[0]
                # separate out short/long key id's
                elif values and x in ['keyid', 'longkeyid']:
                    value = get_key_ids(x, values)
                    if len(value):
                        keyid_found = True
                elif values and x in ['fingerprint']:
                    value = [v.replace(' ', '') for v in values]
                else:
                    value = values
                if 'undefined' in values:
                    self.logger.error('%s = "undefined" for %s, %s'
                        %(field, info['uid'][0], info['cn'][0]))
                keyinfo.append(value)
            except KeyError:
                self.logger.error("Missing %s (%s) for %s, %s"
                    %(field, x, info['uid'][0], info['cn'][0]))
                if x in ['keyid', 'longkeyid']:
                    keyid_missing = True
                keyinfo.append(None)
        if not keyid_found and not keyid_missing:
            try:
                gpgkey = info[gkey2ldap_map['longkeyid']]
            except KeyError:
                gpgkey = 'Missing from ldap info'
            self.logger.error("A valid keyid or longkeyid was not found for")
            self.logger.error("developer: %s, %s : gpgkey = %s"
                %(info['uid'][0], info['cn'][0], gpgkey))
        else:
            for x in [2, 3]:
                if not keyinfo[x]:
                    continue
                for y in keyinfo[x]:
                    index = len(y.lstrip('0x'))
                    if y.lstrip('0x') not in [x[-index:] for x in keyinfo[5]]:
                        self.logger.error('GPGKey and/or fingerprint error in' +
                            ' ladap info for: ' + info['uid'][0])
                        self.logger.error(str(keyinfo))
        return keyinfo

