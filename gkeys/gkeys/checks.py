#
#-*- coding:utf-8 -*-

"""
    Gentoo-Keys - gkeygen/checks.py

    Primary key checks module
    @copyright: 2014 by Brian Dolbec <dolsen@gentoo.org>
    @license: GNU GPL2, see COPYING for details
"""

import time
from collections import namedtuple, OrderedDict

from gkeys.config import GKEY_CHECK

from pyGPG.mappings import (ALGORITHM_CODES, CAPABILITY_MAP,
    KEY_VERSION_FPR_LEN, VALIDITY_MAP, INVALID_LIST,
    VALID_LIST)


SPEC_INDEX = {
    'key': 0,
    'capabilities': 1,
    'fingerprint': 2,
    'bits': 3,
    'created': 4,
    'expire': 5,
    'encrypt_capable': 6,
    'sign_capable': 7,
    'algo': 8,
    'version': 9,
    'id': 10,
    'days': 11,
    'validity': 12,
    'expire_reason': 13,
    'long_caps': 14,  # long version of the capbilities
    'caps': 15,
    'caps_reason': 16,
    'id_reason': 17,
    'is_valid': 18,
    'passed_spec': 19,
}

SPEC_INDEX = OrderedDict(sorted(SPEC_INDEX.items(), key=lambda t: t[1]))

SPEC_STAT = ['', '','', False, False, False, False, False, False, False, False,
    0, '', '', '', True, '', '', False, False]

# Default glep 63 minimum gpg key specification
# and approved options, limits
TEST_SPEC = {
    'bits': {
        'DSA': 2048,
        'RSA': 2048,
        },
    'expire': 3 * 365,      # in days
    'subkeys': {        # warning/error mode
        'encrypt': {
            'mode': 'notice',
            'expire': 3 * 365,
            },
        'sign': {
            'mode': 'error',
            'expire': 365,
            },
        },
    'algorithms': ['DSA', 'RSA', '1', '2', '3', '17'],
    'versions': ['4'],
    'qualified_id': '@gentoo.org',
}

# Final pass/fail fields and the pass value required
TEST_REQUIREMENTS = {
    'bits': True,
    'created': True,
    'expire': True,
    'sign_capable': True,
    'algo': True,
    'version': True,
    'id': True,
    'is_valid': True,
    'caps': True,
}

SECONDS_PER_DAY = 86400


SPECCHECK_STRING = '''    ----------
    Fingerprint......: %(fingerprint)s
    Key type ........: %(key)s    Capabilities.: %(capabilities)s  %(long_caps)s
    Algorithm........: %(algo)s   Bit Length...: %(bits)s
    Create Date......: %(created)s   Expire Date..: %(expire)s
    Key Version......: %(version)s   Validity.....: %(validity)s
    Days till expiry.: %(days)s %(expire_reason)s
    Capability.......: %(caps)s %(caps_reason)s
    Qualified ID.....: %(id)s %(id_reason)s
    This %(pub_sub)s.: %(passed_spec)s'''

SPECCHECK_SUMMARY = '''    Key summary
    primary..........: %(pub)s         signing subkey: %(sign)s
    encryption subkey: %(encrypt)s  authentication subkey: %(auth)s
    SPEC requirements: %(final)s
'''

def convert_pf(data, fields):
    '''Converts dictionary items from True/False to Pass/Fail strings

    @param data: dict
    @param fields: list
    @returns: dict
    '''
    for f in fields:
        if data[f]:
            data[f] = 'Pass'
        else:
            data[f] = 'Fail'
    return data

def convert_yn(data, fields):
    '''Converts dictionary items from True/False to Yes/No strings

    @param data: dict
    @param fields: list
    @returns: dict
    '''
    for f in fields:
        if data[f]:
            data[f] = 'Yes '
        else:
            data[f] = 'No  '
    return data


class SpecCheck(namedtuple("SpecKey", list(SPEC_INDEX))):

    __slots__ = ()

    def pretty_print(self):
        data = self.convert_data()
        output = SPECCHECK_STRING % (data)
        return output


    def convert_data(self):
        data = dict(self._asdict())
        data = convert_pf(data, ['algo', 'bits', 'caps', 'created', 'expire', 'id',
            'passed_spec', 'version'])
        for f in ['caps', 'id']:
            data[f] = data[f].ljust(10)
        data['validity'] += ', %s' % (VALIDITY_MAP[data['validity']])
        days = data['days']
        if days == float("inf"):
            data['days'] = "infinite".ljust(10)
        else:
            data['days'] = str(int(data['days'])).ljust(10)
        if data['capabilities'] == 'e':
            data['algo'] = '----'
            data['bits'] = '----'
        if data['key'] =='PUB':
            data['pub_sub'] = 'primary key'
        else:
            data['pub_sub'] = 'subkey.....'
        return data


class KeyChecks(object):
    '''Primary gpg key validation and specifications checks class'''

    def __init__(self, logger, spec=TEST_SPEC, qualified_id_check=True):
        '''@param spec: optional gpg specification to test against
                        Defaults to TEST_SPEC

        '''
        self.logger = logger
        self.spec = spec
        self.check_id = qualified_id_check


    def validity_checks(self, keydir, keyid, result):
        '''Check the specified result based on the seed type

        @param keydir: the keydir to list the keys for
        @param keyid: the keyid to check
        @param result: pyGPG.output.GPGResult object
        @returns: GKEY_CHECK instance
        '''
        revoked = expired = invalid = sign = False
        for data in result.status.data:
            if data.name ==  "PUB":
                if data.long_keyid == keyid[2:]:
                    # check if revoked
                    if 'r' in data.validity:
                        revoked = True
                        self.logger.debug("ERROR in key %s : revoked" % data.long_keyid)
                        break
                    # if primary key expired, all subkeys expire
                    if 'e' in data.validity:
                        expired = True
                        self.logger.debug("ERROR in key %s : expired" % data.long_keyid)
                        break
                    # check if invalid
                    if 'i' in data.validity:
                        invalid = True
                        self.logger.debug("ERROR in key %s : invalid" % data.long_keyid)
                        break
                    if 's' in data.key_capabilities:
                        sign = True
                        self.logger.debug("INFO primary key %s : key signing capabilities" % data.long_keyid)
            if data.name == "SUB":
                # check if invalid
                if 'i' in data.validity:
                    self.logger.debug("WARNING in subkey %s : invalid" % data.long_keyid)
                    continue
                # check if expired
                if 'e' in data.validity:
                    self.logger.debug("WARNING in subkey %s : expired" % data.long_keyid)
                    continue
                # check if revoked
                if 'r' in data.validity:
                    self.logger.debug("WARNING in subkey %s : revoked" % data.long_keyid)
                    continue
                # check if subkey has signing capabilities
                if 's' in data.key_capabilities:
                    sign = True
                    self.logger.debug("INFO subkey %s : subkey signing capabilities" % data.long_keyid)
        return GKEY_CHECK(keyid, revoked, expired, invalid, sign)


    def spec_check(self, keydir, keyid, result):
        '''Performs the minimum specifications checks on the key'''
        self.logger.debug("SPEC_CHECK() : CHECKING: %s" % keyid)
        results = {}
        pub = None
        stats = None
        pub_days = 0
        for data in result.status.data:
            if data.name ==  "PUB":
                if stats:
                    stats = self._test_final(data, stats)
                    results[pub.long_keyid].append(SpecCheck._make(stats))
                pub = data
                found_id = False
                found_id_reason = ''
                results[data.long_keyid] = []
                stats = SPEC_STAT[:]
                stats[SPEC_INDEX['key']] = data.name
                stats[SPEC_INDEX['capabilities']] = data.key_capabilities
                stats[SPEC_INDEX['validity']] = data.validity
                stats = self._test_created(data, stats)
                stats = self._test_algo(data, stats)
                stats = self._test_bits(data, stats)
                stats = self._test_expire(data, stats, pub_days)
                pub_days = stats[SPEC_INDEX['days']]
                stats = self._test_caps(data, stats)
                stats = self._test_validity(data, stats)
            elif data.name ==  "FPR":
                pub = pub._replace(**{'fingerprint': data.fingerprint})
                stats[SPEC_INDEX['fingerprint']] = data.fingerprint
                stats = self._test_version(data, stats)
            elif data.name ==  "UID":
                stats = self._test_uid(data, stats)
                if stats[SPEC_INDEX['id']] in [True, '-----']:
                    found_id = stats[SPEC_INDEX['id']]
                    found_id_reason = ''
                    stats[SPEC_INDEX['id_reason']] = ''
                else:
                    found_id_reason = stats[SPEC_INDEX['id_reason']]
            elif data.name == "SUB":
                if stats:
                    stats = self._test_final(data, stats)
                    results[pub.long_keyid].append(SpecCheck._make(stats))
                stats = SPEC_STAT[:]
                stats[SPEC_INDEX['key']] = data.name
                stats[SPEC_INDEX['capabilities']] = data.key_capabilities
                stats[SPEC_INDEX['fingerprint']] = '%s' \
                    % (data.long_keyid)
                stats[SPEC_INDEX['id']] = found_id
                stats[SPEC_INDEX['id_reason']] = found_id_reason
                stats[SPEC_INDEX['validity']] = data.validity
                stats = self._test_validity(data, stats)
                stats = self._test_created(data, stats)
                stats = self._test_algo(data, stats)
                stats = self._test_bits(data, stats)
                stats = self._test_expire(data, stats, pub_days)
                stats = self._test_caps(data, stats)
        if stats:
            stats = self._test_final(data, stats)
            results[pub.long_keyid].append(SpecCheck._make(stats))
            stats = None
        self.logger.debug("SPEC_CHECK() : COMPLETED: %s" % keyid)
        return results


    def _test_algo(self, data, stats):
        algo = data.pubkey_algo
        if algo in TEST_SPEC['algorithms']:
            stats[SPEC_INDEX['algo']] = True
        else:
            self.logger.debug("ERROR in key %s : invalid Type: %s"
                % (data.long_keyid, ALGORITHM_CODES[algo]))
        return stats


    def _test_bits(self, data, stats):
        bits = int(data.keylength)
        if data.pubkey_algo in TEST_SPEC['algorithms']:
            if bits >= TEST_SPEC['bits'][ALGORITHM_CODES[data.pubkey_algo]]:
                stats[SPEC_INDEX['bits']] = True
            else:
                self.logger.debug("ERROR in key %s : invalid Bit length: %d"
                    % (data.long_keyid, bits))
        return stats


    def _test_version(self, data, stats):
        fpr_l = len(data.fingerprint)
        if KEY_VERSION_FPR_LEN[fpr_l] in TEST_SPEC['versions']:
            stats[SPEC_INDEX['version']] = True
        else:
            self.logger.debug("ERROR in key %s : invalid gpg key version: %s"
                % (data.long_keyid, KEY_VERSION_FPR_LEN[fpr_l]))
        return stats


    def _test_created(self, data, stats):
        try:
            created = float(data.creation_date)
        except ValueError:
            created = 0
        if created <= time.time() :
            stats[SPEC_INDEX['created']] = True
        else:
            self.logger.debug("ERROR in key %s : invalid gpg key creation date: %s"
                % (data.long_keyid, data.creation_date))
        return stats


    def _test_expire(self, data, stats, pub_days):
        if data.name in ["PUB"]:
            delta_t = TEST_SPEC['expire']
            stats = self._expire_check(data, stats, delta_t, pub_days)
            return stats
        else:
            for cap in data.key_capabilities:
                try:
                    delta_t = TEST_SPEC['subkeys'][CAPABILITY_MAP[cap]]['expire']
                except KeyError:
                    self.logger.debug(
                        "WARNING in capability key %s : setting delta_t to main expiry: %d"
                        % (cap, TEST_SPEC['expire']))
                    delta_t = TEST_SPEC['expire']
                stats = self._expire_check(data, stats, delta_t, pub_days)
                return stats


    def _expire_check(self, data, stats, delta_t, pub_days):
        today = time.time()
        try:
            expires = float(data.expiredate)
        except ValueError:
            expires = float("inf")
        if data.name == 'SUB' and expires == float("inf"):
            days = stats[SPEC_INDEX['days']] = pub_days
        elif expires == float("inf"):
            days = stats[SPEC_INDEX['days']] = expires
        else:
            days = stats[SPEC_INDEX['days']] = max(0, int((expires - today)/SECONDS_PER_DAY))
        if days <= delta_t:
            stats[SPEC_INDEX['expire']] = True
        elif days > delta_t and not ('i' in data.validity or 'r' in data.validity):
            stats[SPEC_INDEX['expire_reason']] = '<== Exceeds specification'
        else:
            self.logger.debug("ERROR in key %s : invalid gpg key expire date: %s"
                % (data.long_keyid, data.expiredate))
        if 0 < days < 30 and not ('i' in data.validity or 'r' in data.validity):
            stats[SPEC_INDEX['expire_reason']] = '<== WARNING < 30 days'

        return stats


    def _test_caps(self, data, stats):
        if 'e' in data.key_capabilities:
            if 's' in data.key_capabilities or 'a' in data.key_capabilities:
                stats[SPEC_INDEX['caps']] = False
                stats[SPEC_INDEX['caps_reason']] = "<== Mixing of 'e' with 's' and/or 'a'"
        if not stats[SPEC_INDEX['is_valid']]:
            return stats
        kcaps = []
        for cap in data.key_capabilities:
            if CAPABILITY_MAP[cap] and stats[SPEC_INDEX['caps']]:
                kcaps.append(CAPABILITY_MAP[cap])
                if cap in ["s"] and not data.name == "PUB":
                    stats[SPEC_INDEX['sign_capable']] = True
                elif cap in ["e"]:
                    stats[SPEC_INDEX['encrypt_capable']] = True
                elif cap not in CAPABILITY_MAP:
                    stats[SPEC_INDEX['caps']] = False
                    self.logger.debug("ERROR in key %s : unknown gpg key capability: %s"
                        % (data.long_keyid, cap))
        stats[SPEC_INDEX['long_caps']] = ', '.join(kcaps)
        return stats


    def _test_uid(self, data, stats):
        if not self.check_id:
            stats[SPEC_INDEX['id']] = '-----'
            stats[SPEC_INDEX['id_reason']] = ''
            return stats
        if TEST_SPEC['qualified_id'] in data.user_ID :
            stats[SPEC_INDEX['id']] = True
            stats[SPEC_INDEX['id_reason']] = ''
        else:
            stats[SPEC_INDEX['id_reason']] = "<== '%s' user id not found" % TEST_SPEC['qualified_id']
            self.logger.debug("Warning: No qualified ID found in key %s"
                % (data.user_ID))
        return stats


    def _test_validity(self, data, stats):
        if data.validity in VALID_LIST:
            stats[SPEC_INDEX['is_valid']] = True
        return stats


    def _test_final(self, data, stats):
        for test, result in TEST_REQUIREMENTS.items():
            if ((stats[SPEC_INDEX['key']] == 'PUB' and test == 'sign_capable') or
                (stats[SPEC_INDEX['capabilities']] == 'e' and test in ['algo', 'bits', 'sign_capable'])
                or (stats[SPEC_INDEX['capabilities']] == 'a' and test in ['sign_capable'])):
                continue
            if stats[SPEC_INDEX[test]] == result:
                stats[SPEC_INDEX['passed_spec']] = True
            else:
                stats[SPEC_INDEX['passed_spec']] = False
                break
        return stats
