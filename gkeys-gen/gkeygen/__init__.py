#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict

from gkeygen.actions import Action_Map, Available_Actions


__version__ = 'Git'
__license__ = 'GPLv2'


subdata = OrderedDict()
for cmd in Available_Actions:
    subdata[cmd] = Action_Map[cmd]['desc']

Gkeys_Map = {
    'options': ['help', 'config', 'debug'],
    'desc': 'OpenPGP/GPG key generator tool',
    'long_desc': '''Gentoo Keys (gkeys) is a Python based project that aims to manage
the GPG keys used for validation on users and Gentoo's infrastracutre servers.
Gkeys-gen is a tool for generating OpnPGP/GPG keys according to a selected spec.''',
    'sub-cmds': subdata,
    'authors': ['Brian Dolbec <dolsen@gentoo.org>', 'Pavlos Ratis <dastergon@gentoo.org>'],
}
