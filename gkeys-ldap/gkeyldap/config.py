#
#-*- coding:utf-8 -*-


default_server = 'ldap://ldap1.gentoo.org'
# add uid to the results so you don't have to
# separate it out of the results tuple[0] value
default_fields = ['uid', 'cn', 'mail', 'gentooStatus', 'gpgkey', 'gpgfingerprint']
default_criteria = 'ou=devs,dc=gentoo,dc=org'

# establish a ldap fields to GKEY._fields map
gkey2ldap = {
    'nick': 'uid',
    'name': 'cn',
    'keyid': 'gpgkey',
    'longkeyid': 'gpgkey',
    # map the uid to keydir, since we want
    # dev keydir to be separate from each other
    'keydir': 'uid',
    'fingerprint': 'gpgfingerprint'
}


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
