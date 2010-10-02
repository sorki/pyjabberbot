#!/usr/bin/env python

import os
from distutils.core import setup

NAME = 'pyjabberbot'
VERSION = '0.6'
WEBSITE = 'http://github.com/sorki/pyjabberbot'
LICENSE = 'GPLv3 or later'
DESCRIPTION = 'Pyjabberbot, powerful xmpp bot implementation'

AUTHOR = 'Richard Marko'
EMAIL = 'rissko@gmail.com'

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as fh:
    LONG_DESCRIPTION = fh.read().strip()

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('pyjabberbot'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[12:] # Strip "pyjabberbot/" or "pyjabberbot\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))


setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=EMAIL,
      license=LICENSE,
      url=WEBSITE,
      package_dir={'pyjabberbot': 'pyjabberbot'},
      packages=packages,
      package_data={'pyjabberbot': data_files},
      classifiers=['Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Topic :: Software Development'],
      )
