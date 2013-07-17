#
#-*- coding:utf-8 -*-


import ldap

from gkeys import log
from gkeys.config import GKEY

logger = log.logger

default_server = 'ldap://ldap1.gentoo.org'
# add uid to the results so you don't have to
# separate it out of the results tuple[0] value
default_fields = ['uid', 'cn', 'mail', 'gentooStatus', 'gpgkey', 'gpgfingerprint']
default_criteria = 'ou=devs,dc=gentoo,dc=org'

# establish a ldap fields to GKEY._fields map
gkey2ldap_map = {
    'nick': 'uid',
    'name': 'cn',
    'keyid': 'gpgkey',
    'longkeyid': 'gpgkey',
    # map the uid to keydir, since we want
    # dev keydir to be separate from each other
    'keydir': 'uid',
    'fingerprint': 'gpgfingerprint'
}
# Sanity check they are in sync
if not sorted(gkey2ldap_map) == sorted(GKEY._fields):
    raise "Search.py out of sync with GKEY class"


# Now for some search field defaults
UID = '(uid=%s)'
CN = '(cn=%s)'
STATUS = '(gentooStatus=%s)'
GPGKEY = '(gpgkey=%s)'
MAIL = '(mail=%s)'
GPGFINGERPRINT = '(gpgfingerprint=%s)'

gkey2SEARCH = {
    'nick': UID,
    'name': CN,
    'status': STATUS,
    'keyid': GPGKEY,
    'mail': MAIL,
    'fingerprint': GPGFINGERPRINT,
}


class LdapSearch(object):
    '''Class to perform searches on the configured ldap server
    '''

    def __init__(self, server=None, fields=None, criteria=None):
        self.server = server or default_server
        self.fields = fields or default_fields
        self.criteria = criteria or default_criteria
        logger.debug('LdapSearch: __init__; server...: %s' % self.server)
        logger.debug('LdapSearch: __init__; fields...: %s' % self.fields)
        logger.debug('LdapSearch: __init__; criteria.: %s' % self.criteria)
        self.ldap_connection = None


    def connect(self, server=None,):
        '''Creates our ldap server connection

        '''
        if server:
            self.server = server
            logger.debug('LdapSearch: connect; new server: %s' % self.server)
        try:
            self.ldap_connection = ldap.initialize(self.server)
            self.ldap_connection.set_option(ldap.OPT_X_TLS_DEMAND, True)
            self.ldap_connection.start_tls_s()
            self.ldap_connection.simple_bind_s()
        except Exception as e:
            logger.error('LdapSearch: connect; failed to connect to server: %s' % self.server)
            logger.error("Exception was: %s" % str(e))
            return False
        logger.debug('LdapSearch: connect; connection: %s' % self.ldap_connection)
        return True



    def search(self, target, search_field=UID, fields=None, criteria=None):
        '''Perform the ldap search
        '''
        if not target:
            logger.debug('LdapSearch: search; invalid target: "%s"' % target)
            return {}
        if not fields:
            fields = self.fields
        else:
            logger.debug('LdapSearch: search; new fields: %s' % str(fields))
        if not criteria:
            criteria = self.criteria
        else:
            logger.debug('LdapSearch: search; new criteria: %s' % criteria)
        results = self.ldap_connection.search_s(criteria,
            ldap.SCOPE_ONELEVEL, search_field % target, fields)
        #logger.debug('LdapSearch: search; result = %s' % str(results))
        return results


    def result2dict(self, results, key='uid'):
        _dict = {}
        for entry in results:
            info = entry[1]
            key_value = info[key][0]
            _dict[key_value] = info
        return _dict
