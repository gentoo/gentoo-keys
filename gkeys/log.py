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


NAMESPACE = 'gentoo-keys'
logger = None
Console_handler = None
File_handler = None

log_levels = {
    'CRITICAL': logging.CRITICAL,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
    'INFO': logging.INFO,
    'NOTSET': logging.NOTSET,
    'WARN': logging.WARN,
    'WARNING':logging.WARNING,
}



def set_logger(namespace=None, logpath='', level=None):
    global logger, NAMESPACE, Console_handler, File_handler
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
        logname = os.path.join(logpath,
            '%s-%s.log' % (namespace,time.strftime('%Y%m%d-%H:%M')))
        File_handler = logging.FileHandler(logname)
        if level:
            #print "Setting cli log level", level, log_levels[level]
            File_handler.setLevel(log_levels[level])
        else:
            #print "Create file handler which logs even debug messages"
            File_handler.setLevel(log_levels['DEBUG'])

    File_handler.setFormatter(formatter)
    # create console handler with a higher log level
    Console_handler = logging.StreamHandler()
    Console_handler.setLevel(logging.ERROR)
    #Console_handler.setFormatter(formatter)
    logger.addHandler(Console_handler)
    logger.addHandler(File_handler)
    #print "File logger suppose to be initialized", logger, File_handler, Console_handler
    logger.debug("Loggers initialized")

    return logger




