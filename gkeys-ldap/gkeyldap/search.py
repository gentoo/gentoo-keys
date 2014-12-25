#
#-*- coding:utf-8 -*-


try:
    import ldap
except ImportError:
    import sys
    # py3.2
    if sys.hexversion >= 0x30200f0:
        print('To run "ldap-seeds" in python 3, it requires a python3 '
            'compatible version of dev-python/python-ldap be installed\n'
            'Currently only dev-python/python-ldap-9999 has that capability.')
        raise


from gkeyldap.config import default_criteria, default_fields, UID
from gkeyldap.connect import LdapConnect

class LdapSearch(object):
    '''Class to perform searches on the configured LDAP server
    '''

    def __init__(self, fields=None, criteria=None, logger=None):
        self.fields = fields or default_fields
        self.criteria = criteria or default_criteria
        self.logger = logger
        self.logger.debug('LdapSearch: __init__; fields...: %s' % self.fields)
        self.logger.debug('LdapSearch: __init__; criteria.: %s' % self.criteria)
        self.ldap_connection = LdapConnect().connect(action='Search')
        self.status = True
        if not self.ldap_connection:
            self.status = False

    def search(self, target, search_field=UID, fields=None, criteria=None):
        '''Perform the LDAP search
        '''
        if not target:
            self.logger.debug('LdapSearch: search; invalid target: "%s"' % target)
            return {}
        if not fields:
            fields = self.fields
        else:
            self.logger.debug('LdapSearch: search; new fields: %s' % str(fields))
        if not criteria:
            criteria = self.criteria
        else:
            self.logger.debug('LdapSearch: search; new criteria: %s' % criteria)
        results = self.ldap_connection.search_s(criteria,
            ldap.SCOPE_ONELEVEL, search_field % target, fields)
        #self.logger.debug('LdapSearch: search; result = %s' % str(results))
        return results


    def result2dict(self, results, key='uid'):
        ''' Convert results from LDAP attributes
         to Gentoo Keys compatible attributes

         @param results: dictionary with results
         @param key: string to use as a key in the dictionary
        '''

        _dict = {}
        for entry in results:
            info = entry[1]
            key_value = info[key][0]
            _dict[key_value] = info
        return _dict
