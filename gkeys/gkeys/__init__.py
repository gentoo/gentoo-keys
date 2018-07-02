#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys

from collections import OrderedDict

from gkeys.action_map import Action_Map, Available_Actions


__version__ = '0.2'
__license__ = 'GPLv2'

if sys.version_info[0] >= 3:
    py_input = input
    _unicode = str
else:
    py_input = raw_input
    _unicode = unicode


subdata = OrderedDict()
for cmd in Available_Actions:
    subdata[cmd] = Action_Map[cmd]['desc']

Gkeys_Map = {
    'options': ['help', 'config', 'debug', 'version'],
    'desc': 'OpenPGP/GPG key management tool',
    'long_desc': '''Gentoo Keys (gkeys) is a Python based project that aims to manage
the GPG keys used for validation on users and Gentoo's infrastracutre servers.
Gentoo Keys is able to verify GPG keys used for Gentoo's release media,
such as installation CD's, Live DVD's, packages and other GPG signed documents.''',
    'sub-cmds': subdata,
    'authors': ['Brian Dolbec <dolsen@gentoo.org>', 'Pavlos Ratis <dastergon@gentoo.org>'],
}
