#!/usr/bin/env python

import os
import sys

from distutils.core import setup
from gkeygen import __version__, __license__

# this affects the names of all the directories we do stuff with
sys.path.insert(0, './')

#__version__ = os.getenv('VERSION', default='9999')

# Load EPREFIX from Portage, fall back to the empty string if it fails
try:
    from portage.const import EPREFIX
except ImportError:
    EPREFIX=''


setup(
    name='gkeygen',
    version=__version__,
    description="Gentoo gpg key management key generator",
    author='',
    author_email='',
    maintainer='Gentoo-Keys Team',
    maintainer_email='gkeys@gentoo.org',
    url="https://wiki.gentoo.org/wiki/Project:Gentoo-keys",
    download_url='',
    packages=['gkeyldap'],
    scripts=['bin/gkey-ldap'],
    license=__license__,
    long_description=open('README.md').read(),
    keywords='gpg',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers, Users',
        'License :: OSI Approved :: GPLv2 License',
        'Programming Language :: Python :: 2.7, 3.3, 3.4, +',
        'Operating System :: OS Independent',
        'Topic :: Security :: Cryptography',
    ],
)
