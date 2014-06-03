#
#-*- coding:utf-8 -*-

"""
    Gentoo-keys - gkeyldap/actions.py

    Primary api interface module

    @copyright: 2012 by Brian Dolbec <dol-sen@gentoo.org>
    @license: GNU GPL2, see COPYING for details.
"""

import os
import re

from collections import defaultdict
from gkeys.seed import Seeds
from gkeyldap.search import (LdapSearch, UID, gkey2ldap_map, gkey2SEARCH)


Available_Actions = ['ldapsearch', 'updateseeds']


def get_key_ids(key_len, keyids):
    '''Small utility function to return only keyid (short)
    or longkeyid's

    @param key_len: string, the key length desired
    @param keyids: list of keysid's to process
    @return list of the desired key length id's
    '''
    result = []
    for keyid in keyids:
        target_len = 16
        if keyid.startswith('0x'):
            target_len = target_len + 2
        if len(keyid) == target_len:
            result.append(keyid)
    return result


class Actions(object):


    def __init__(self, config, output=None, logger=None):
        self.config = config
        self.output = output
        self.logger = logger
        self.seeds = None
        self.fingerprint_re = re.compile('[0-9A-Fa-f]{40}')


    def ldapsearch(self, args):
        l = LdapSearch()
        self.logger.info("Search... Establishing connection")
        self.output("Search... Establishing connection")
        if not l.connect():
            self.logger.info("Aborting search... Connection failed")
            self.output("Aborting search... Connection failed")
            return False
        self.logger.debug("MAIN: _action_ldapsearch; args = %s" % str(args))
        x, target, search_field = self.get_args(args)
        results = l.search(target, search_field)
        devs = l.result2dict(results, gkey2ldap_map[x])
        for dev in sorted(devs):
            self.output(dev, devs[dev])
        self.output("============================================")
        self.output("Total number of developers in results:", len(devs))
        self.logger.info("============================================")
        self.logger.info("Total number of developers in results: %d" % len(devs))
        return True


    def updateseeds(self, args):
        self.logger.info("Beginning LDAP search...")
        self.output("Beginning LDAP search...")
        l = LdapSearch()
        if not l.connect():
            self.output("Aborting update... Connection failed")
            self.logger.info("Aborting update... Connection failed")
            return False
        results = l.search('*', UID)
        info = l.result2dict(results, 'uid')
        self.logger.debug(
            "MAIN: _action_updateseeds; got results :) converted to info")
        if not self.create_seedfile(info):
            self.logger.error("Developer seed file update failure: "
                "Original seed file is intact & untouched.")
        filename = self.config['dev-seedfile']
        old = filename + '.old'
        try:
            self.output("Backing up existing file...")
            self.logger.info("Backing up existing file...")
            if os.path.exists(old):
                self.logger.debug(
                    "MAIN: _action_updateseeds; Removing 'old' seed file: %s"
                    % old)
                os.unlink(old)
            if os.path.exists(filename):
                self.logger.debug(
                    "MAIN: _action_updateseeds; Renaming current seed file to: "
                    "%s" % old)
                os.rename(filename, old)
            self.logger.debug(
                "MAIN: _action_updateseeds; Renaming '.new' seed file to: %s"
                % filename)
            os.rename(filename + '.new', filename)
        except IOError:
            raise
        self.output("Developer seed file updated!")
        return True


    def create_seedfile(self, devs):
        self.output("Creating seeds from LDAP data...")
        filename = self.config['dev-seedfile'] + '.new'
        self.seeds = Seeds(filename)
        count = 0
        error_count = 0
        for dev in sorted(devs):
            if devs[dev]['gentooStatus'][0] not in ['active']:
                continue
            #self.logger.debug("create_seedfile, dev = "
            #   "%s, %s" % (str(dev), str(devs[dev])))
            developer_attrs = self.build_gkeydict(devs[dev])
            if developer_attrs:
                self.seeds.add(dev, developer_attrs)
                count += 1
            else:
                error_count += 1
        self.output("Total number of seeds created:", count)
        self.output("Seeds created... Saving file: %s" % filename)
        self.output("Total number of Dev's with GPG errors:", error_count)
        self.logger.info("Total number of seeds created: %d" % count)
        self.logger.info("Seeds created... Saving file: %s" % filename)
        self.logger.info("Total number of Dev's with GPG errors: %d" % error_count)
        return self.seeds.save()


    @staticmethod
    def get_args(args):
        for attr in ['nick', 'name', 'gpgkey', 'fingerprint', 'status']:
            if attr:
                target = getattr(args, attr)
                search_field = gkey2SEARCH[attr]
                break
        return (attr, target, search_field)


    def build_gkeydict(self, info):
        keyinfo = defaultdict()
        keyid_found = False
        keyid_missing = False
        # assume it's good until an error is found
        is_good = True
        #self.logger.debug("Actions: build_gkeylist; info = %s" % str(info))
        for attr in gkey2ldap_map:
            field = gkey2ldap_map[attr]
            if not field:
                keyinfo[attr] = None
                continue
            try:
                values = info[field]
                # strip errant line feeds
                values = [y.strip('\n') for y in values]
                # separate out short/long key id's
                if values and attr in ['keyid', 'longkeyid']:
                    if len(get_key_ids(attr, values)):
                        keyid_found = True
                elif values and attr in ['fingerprint']:
                    values = [v.replace(' ', '') for v in values]
                if 'undefined' in values:
                    self.logger.error('ERROR in LDAP info for: %s, %s'
                        % (info['uid'][0],info['cn'][0]))
                    self.logger.error('  %s = "undefined"' % (field))
                    is_good = False
                keyinfo[attr] = values
            except KeyError:
                self.logger.debug('LDAP info for: %s, %s'
                    % (info['uid'][0],info['cn'][0]))
                self.logger.debug('  MISSING or EMPTY LDAP field ' +
                    '[%s] GPGKey field [%s]' % (field, attr))
                if attr in ['keyid', 'longkeyid']:
                    keyid_missing = True
                else:
                    is_good = False
                keyinfo[attr] = None
        if not keyid_found and keyid_missing:
            fingerprint = None
            try:
                fingerprint = info[gkey2ldap_map['fingerprint']]
                self.logger.debug('  Generate gpgkey, Found LDAP fingerprint field')
            except KeyError:
                gpgkey = 'Missing fingerprint from LDAP info'
                self.logger.debug('  Generate gpgkey, LDAP fingerprint KeyError')
            if fingerprint:
                values = [y.strip('\n') for y in fingerprint]
                values = [v.replace(' ', '') for v in values]
                # assign it to gpgkey to prevent a possible
                # "gpgkey" undefined error
                gpgkey = ['0x' + x[-16:] for x in values]
                keyinfo['longkeyid'] = gpgkey
                self.logger.debug('  Generate gpgkey, NEW keyinfo[\'fingerprint\'] = %s'
                    % str(keyinfo['longkeyid']))
            else:
                gpgkey = 'Missing or Bad fingerprint from LDAP info'
                is_good = False
            if not keyinfo['longkeyid']:
                self.logger.error('ERROR in ldap info for: %s, %s'
                    %(info['uid'][0],info['cn'][0]))
                self.logger.error('  A valid keyid, longkeyid or fingerprint '
                    'was not found for %s : gpgkey = %s' %(info['cn'][0], gpgkey))
                is_good = False
        if is_good:
            if keyinfo['fingerprint']: # fingerprints exist check
                is_ok = self._check_fingerprint_integrity(info, keyinfo)
                is_match = self._check_id_fingerprint_match(info, keyinfo)
                if not is_ok or not is_match:
                    is_good = False
        if is_good:
            # drop keyid and longkeyid
            keyinfo.pop('keyid', None)
            keyinfo.pop('longkeyid', None)
            return keyinfo
        return None


    def _check_id_fingerprint_match(self, info, keyinfo):
        # assume it's good until found an error is found
        is_good = True
        for attr in ['keyid', 'longkeyid']:
            # skip blank id field
            if not keyinfo[attr]:
                continue
            for y in keyinfo[attr]:
                index = len(y.lstrip('0x'))
                if y.lstrip('0x').upper() not in \
                        [x[-index:].upper() for x in keyinfo['fingerprint']]:
                    self.logger.error('ERROR in LDAP info for: %s, %s'
                        %(info['uid'][0],info['cn'][0]))
                    self.logger.error('  ' + str(keyinfo))
                    self.logger.error('  GPGKey id %s not found in the '
                        % y.lstrip('0x') + 'listed fingerprint(s)')
                    is_good = False
        return is_good


    def _check_fingerprint_integrity(self, info, keyinfo):
        # assume it's good until found an error is found
        is_good = True
        for fingerprint in keyinfo['fingerprint']:
            # check fingerprint integrity
            if len(fingerprint) != 40:
                self.logger.error('ERROR in LDAP info for: %s, %s'
                    %(info['uid'][0],info['cn'][0]))
                self.logger.error('  GPGKey incorrect fingerprint ' +
                    'length (%s) for fingerprint: %s' %(len(fingerprint), fingerprint))
                is_good = False
                continue
            if not self.fingerprint_re.match(fingerprint):
                self.logger.error('ERROR in LDAP info for: %s, %s'
                    % (info['uid'][0],info['cn'][0]))
                self.logger.error('  GPGKey: Non hexadecimal digits in ' +
                    'fingerprint for fingerprint: ' + fingerprint)
                is_good = False
        return is_good
