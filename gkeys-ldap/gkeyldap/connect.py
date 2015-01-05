#
#-*- coding:utf-8 -*-


try:
    import ldap
except ImportError:
    import sys
    # py3.2
    if sys.hexversion >= 0x30200f0:
        print('To run "ldap-seeds" in python 3, it requires a python3 '
            'compatible version of dev-python/python-ldap be installed.\n'
            'Currently only dev-python/python-ldap-9999 has that capability.')
        raise


from gkeyldap.config import default_server

class LdapConnect(object):
    '''Class to connect on the configured LDAP server'''

    def __init__(self, server=None, logger=None):
        self.server = server or default_server[0]
        self.logger = logger
        self.logger.debug('LdapConnect: __init__; server...: %s' % self.server)
        self.ldap_connection = None

    def connect(self, server=None, action='LDAP'):
        '''Creates our LDAP server connection

        @param server: string URI path for the LDAP server
        '''
        self.logger.info("%s... Establishing connection" % action)
        if server:
            self.server = server
            self.logger.debug('LdapConnect: connect; new server: %s' % self.server)
        connection = True
        for ldap_slave in self.server:
            try:
                self.ldap_connection = ldap.initialize(self.server)
                self.ldap_connection.set_option(ldap.OPT_X_TLS_DEMAND, True)
                self.ldap_connection.start_tls_s()
                self.ldap_connection.simple_bind_s()
            except Exception as e:
                self.logger.error(
                    'LdapConnect: connect; failed to connect to server: %s' % self.server)
                self.logger.error("Exception was: %s" % str(e))
                self.logger.error("Connecting to the next LDAP slave...")
                connection = False
                continue
        if not connection:
            return False
        self.logger.debug(
            'LdapConnect: connect; connection: %s' % self.ldap_connection)
        return self.ldap_connection
