#!/usr/bin/env python


import os
import sys

from distutils.core import setup, Command
from distutils.command.build import build
from distutils.command.sdist import sdist
from glob import glob

from gkeys import __version__, __license__

from gkeys import Gkeys_Map
from gkeys.action_map import Action_Map, Available_Actions

from py2man import manpages


# this affects the names of all the directories we do stuff with
sys.path.insert(0, './')

#__version__ = os.getenv('VERSION', default='9999')

# Load EPREFIX from Portage, fall back to the empty string if it fails
try:
    from portage.const import EPREFIX
except ImportError:
    EPREFIX=''


class x_build(build):
    """ Build command with extra build_man call. """

    def run(self):
        build.run(self)
        self.run_command('build_man')


class build_man(Command):
    """ Perform substitutions in manpages. """

    user_options = [
    ]

    def initialize_options(self):
        self.build_base = None

    def finalize_options(self):
        self.set_undefined_options('build',
            ('build_base', 'build_base'))

    def run(self):
        # create the main page
        basepath = os.path.dirname(__file__)
        docpath = os.path.join(basepath, 'doc')
        templatepath = os.path.dirname(manpages.__file__)
        man = manpages.ManPage('gkeys', __version__, None,
            docpath, Gkeys_Map['authors'])
        man.read_template(templatepath, 'command.template')
        man.make_prog(Gkeys_Map)
        man.read_template(templatepath, 'sub-command.template')
        man.make_subpages(Action_Map, Available_Actions)


class x_sdist(sdist):
    """ sdist defaulting to .tar.bz2 format """

    def finalize_options(self):
        if self.formats is None:
            self.formats = ['bztar']

        sdist.finalize_options(self)


setup(
    name='gkeys',
    version=__version__,
    description="Gentoo gpg key management and Python interface to gpg",
    author='',
    author_email='',
    maintainer='Gentoo-Keys Team',
    maintainer_email='gkeys@gentoo.org',
    url="https://wiki.gentoo.org/wiki/Project:Gentoo-keys",
    download_url='',
    packages=['gkeys'],
    scripts=['bin/gkeys'],
    data_files=[
        (os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'etc/gkeys/'), ['etc/gkeys.conf']),
        (os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'etc/gkeys/'), ['etc/gkeys.conf.sample']),
        (os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'usr/share/man/man1'), glob('doc/*')),
        ],
    license=__license__,
    long_description=open('README.md').read(),
    keywords='gpg',
    cmdclass = {
        'build': x_build,
        'build_man': build_man,
        'sdist': x_sdist,
        },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers, Users',
        'License :: OSI Approved :: GPLv2 License',
        'Programming Language :: Python :: 2.7, 3.3, 3.4, +',
        'Operating System :: OS Independent',
        'Topic :: Security :: Cryptography',
    ],
)
