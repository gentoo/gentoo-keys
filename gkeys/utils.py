#
# -*- coding: utf-8 -*-

'''# File:       utils.py

             Utilities to deal with things...
             copied/edited from app-portage/layman's xml.py


 Copyright:
             (c) 2005 - 2008 Gunnar Wrobel
             (c) 2009        Sebastian Pipping
             (c) 2009        Christian Groschupp
             Distributed under the terms of the GNU General Public License v2

 Author(s):
             Gunnar Wrobel <wrobel@gentoo.org>
             Sebastian Pipping <sebastian@pipping.org>
             Christian Groschupp <christian@groschupp.org>

Utility functions'''



import types
import re
import os
import sys
import locale
import codecs

try:
    StringTypes = types.StringTypes
except AttributeError:
    StringTypes = [str]


def encoder(text, _encoding_):
    return codecs.encode(text, _encoding_, 'replace')


def decode_selection(selection):
    '''utility function to decode a list of strings
    accoring to the filesystem encoding
    '''
    # fix None passed in, return an empty list
    selection = selection or []
    enc = sys.getfilesystemencoding()
    if enc is not None:
        return [encoder(i, enc) for i in selection]
    return selection


def get_encoding(output):
    if hasattr(output, 'encoding') \
            and output.encoding != None:
        return output.encoding
    else:
        encoding = locale.getpreferredencoding()
        # Make sure that python knows the encoding. Bug 350156
        try:
            # We don't care about what is returned, we just want to
            # verify that we can find a codec.
            codecs.lookup(encoding)
        except LookupError:
            # Python does not know the encoding, so use utf-8.
            encoding = 'utf_8'
        return encoding


def pad(string, length):
    '''Pad a string with spaces.'''
    if len(string) <= length:
        return string + ' ' * (length - len(string))
    else:
        return string[:length - 3] + '...'


def terminal_width():
    '''Determine width of terminal window.'''
    try:
        width = int(os.environ['COLUMNS'])
        if width > 0:
            return width
    except:
        pass
    try:
        import struct, fcntl, termios
        query = struct.pack('HHHH', 0, 0, 0, 0)
        response = fcntl.ioctl(1, termios.TIOCGWINSZ, query)
        width = struct.unpack('HHHH', response)[1]
        if width > 0:
            return width
    except:
        pass
    return 80


# From <http://effbot.org/zone/element-lib.htm>
# BEGIN
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
# END

def path(path_elements):
    '''
    Concatenate a path from several elements.

    >>> path([])
    ''
    >>> path(['a'])
    'a'
    >>> path(['a','b'])
    'a/b'
    >>> path(['a/','b'])
    'a/b'
    >>> path(['/a/','b'])
    '/a/b'
    >>> path(['/a/','b/'])
    '/a/b'
    >>> path(['/a/','b/'])
    '/a/b'
    >>> path(['/a/','/b/'])
    '/a/b'
    >>> path(['/a/','/b','c/'])
    '/a/b/c'
    '''
    pathname = ''

    if type(path_elements) in StringTypes:
        path_elements = [path_elements]

    # Concatenate elements and seperate with /
    for i in path_elements:
        pathname += i + '/'

    # Replace multiple consecutive slashes
    pathname = re.compile('/+').sub('/', pathname)

    # Remove the final / if there is one
    if pathname and pathname[-1] == '/':
        pathname = pathname[:-1]

    return pathname


if __name__ == '__main__':
    import doctest
    doctest.testmod(sys.modules[__name__])
