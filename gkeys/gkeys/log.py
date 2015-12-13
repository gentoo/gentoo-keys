#
#-*- coding:utf-8 -*-

"""
    Gentoo-Keys - Log.py

    Logging module, placeholder for our site-wide logging module

    @copyright: 2012 by Brian Dolbec <dol-sen> <dol-sen@users.sourceforge.net>
    @license: GNU GPL2, see COPYING for details.
"""

import logging
import time
import os

from gkeys.fileops import ensure_dirs


NAMESPACE = 'gentoo-keys'
logger = None
Console_handler = None
logname = None

log_levels = {
    'CRITICAL': logging.CRITICAL,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
    'INFO': logging.INFO,
    'NOTSET': logging.NOTSET,
    'WARN': logging.WARN,
    'WARNING': logging.WARNING,
}


def set_logger(namespace=None, logpath='', level=None,
               dirmode=0o775, filemask=0o002):
    global logger, NAMESPACE, Console_handler, logname
    if not namespace:
        namespace = NAMESPACE
    else:
        NAMESPACE = namespace
    logger = logging.getLogger(namespace)
    logger.setLevel(log_levels['DEBUG'])
    # create formatter and add it to the handlers
    log_format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(log_format)
    # add the handlers to logger
    if logpath:
        ensure_dirs(logpath, mode=dirmode, fatal=True)
        os.umask(filemask)
        logname = os.path.join(logpath,
            '%s-%s.log' % (namespace, time.strftime('%Y%m%d-%H:%M')))
        file_handler = logging.FileHandler(logname)
        if level:
            file_handler.setLevel(log_levels[level])
        else:
            file_handler.setLevel(log_levels['DEBUG'])
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # create console handler with a higher log level
    Console_handler = logging.StreamHandler()
    Console_handler.setLevel(logging.ERROR)
    #Console_handler.setFormatter(formatter)
    logger.addHandler(Console_handler)
    #print "File logger suppose to be initialized", logger, Console_handler
    logger.debug("Loggers initialized")

    return logger


def save_logname():
    global logname, NAMESPACE
    _dir, name = os.path.split(logname)
    with open(os.path.join(_dir, '%s-lastlog' % NAMESPACE), 'w') as last:
        last.write(name)


