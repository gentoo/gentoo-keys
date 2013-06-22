#
#-*- coding:utf-8 -*-

"""
    Gentoo-Keys - Log.py

    Logging module, placeholder for our site-wide logging module

    @copyright: 2012 by Brian Dolbec <dol-sen> <dol-sen@users.sourceforge.net>
    @license: GNU GPL2, see COPYING for details.
"""

import logging

logging.basicConfig()

NAMESPACE = 'gentoo-keys'
logger = None

def set_logger(namespace=None):
    global logger, NAMESPACE
    if not namespace:
        namespace = Namespace
    else:
        NAMESPACE = namespace
    logger = logging.getLogger(namespace)


