#!/usr/bin/env python


import collections
import os
import sys

from distutils.core import setup, Command
from distutils.command.build import build

from gkeygen import __version__, __license__

from gkeygen import Gkeys_Map
from gkeygen.actions import Action_Map, Available_Actions

try:
    from py2man import manpages
except ImportError:
    print('creating py2man symlink')
    os.symlink('../py2man', 'py2man')
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
        man = manpages.ManPage('gkey-gen', __version__, None,
            docpath, Gkeys_Map['authors'])
        man.read_template(templatepath, 'command.template')
        man.make_prog(Gkeys_Map)
        man.read_template(templatepath, 'sub-command.template')
        man.make_subpages(Action_Map, Available_Actions)


def get_manpages():
    linguas = os.environ.get('LINGUAS')
    if linguas is not None:
        linguas = linguas.split()

    for dirpath, dirnames, filenames in os.walk('doc'):
        groups = collections.defaultdict(list)
        for f in filenames:
            fn, suffix = f.rsplit('.', 1)
            groups[suffix].append(os.path.join(dirpath, f))

        topdir = dirpath[len('doc/'):]
        if not topdir or linguas is None or topdir in linguas:
            for g, mans in groups.items():
                yield [os.path.join('$mandir', topdir, 'man%s' % g), mans]


setup(
    name='gkeys-gen',
    version=__version__,
    description="OpenPGP/GPG key generator",
    author='',
    author_email='',
    maintainer='Gentoo-Keys Team',
    maintainer_email='gkeys@gentoo.org',
    url="https://wiki.gentoo.org/wiki/Project:Gentoo-keys",
    download_url='',
    packages=['gkeygen'],
    scripts=['bin/gkey-gen'],
    data_files=list(get_manpages()) + [
        (os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'etc/gkeys/'), ['etc/gkeys-gen.conf']),
        ],
    license=__license__,
    long_description=open('README.md').read(),
    keywords='gpg',
    cmdclass = {
        'build': x_build,
        'build_man': build_man,
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
