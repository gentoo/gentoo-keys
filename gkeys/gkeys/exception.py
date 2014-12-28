# Copyright 1998-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2


import sys


if sys.version_info[0] >= 3:
    # pylint: disable=W0622
    basestring = str

    def _unicode_encode(s, encoding='utf_8', errors='backslashreplace'):
        if isinstance(s, str):
            s = s.encode(encoding, errors)
        return s

    def _unicode_decode(s, encoding='utf_8', errors='replace'):
        if isinstance(s, bytes):
            s = str(s, encoding=encoding, errors=errors)
        return s

else:

    def _unicode_encode(s, encoding='utf_8', errors='backslashreplace'):
        if isinstance(s, unicode):
            s = s.encode(encoding, errors)
        return s

    def _unicode_decode(s, encoding='utf_8', errors='replace'):
        if isinstance(s, bytes):
            s = unicode(s, encoding=encoding, errors=errors)
        return s


class GkeysException(Exception):
    if sys.version_info[0] >= 3:
        def __init__(self, value):
            self.value = value[:]

        def __str__(self):
            if isinstance(self.value, str):
                return self.value
            else:
                return repr(self.value)
    else:
        def __init__(self, value):
            self.value = value[:]
            if isinstance(self.value, basestring):
                self.value = _unicode_decode(self.value,
                    encoding='utf_8', errors='replace')

        def __unicode__(self):
            if isinstance(self.value, unicode):
                return self.value
            else:
                return _unicode_decode(repr(self.value),
                    encoding='utf_8', errors='replace')

        def __str__(self):
            if isinstance(self.value, unicode):
                return _unicode_encode(self.value,
                    encoding='utf_8', errors='backslashreplace')
            else:
                return repr(self.value)


class UpdateDbError(GkeysException):
    '''%s

    Please Run: 'gkeys refresh-key -C {foo}'
    on all installed keyring categories
    Then continue with normal gkey operations.'''
    def __init__(self, value):
        doc = self.__doc__ % (value)
        GkeysException.__init__(self, doc)



