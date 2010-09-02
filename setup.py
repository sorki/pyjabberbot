#!/usr/bin/env python
# Setup script for python-jabberbot
# by Thomas Perl <thpinfo.com>

from distutils.core import setup

import os
import re
import sys

# Make sure that we import the local jabberbot module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jabberbot


# How is the package going to be called?
PACKAGE = 'jabberbot'

# List the modules that need to be installed/packaged
MODULES = (
        'jabberbot',
)

# These metadata fields are simply taken from the Jabberbot module
VERSION = jabberbot.__version__
WEBSITE = jabberbot.__website__
LICENSE = jabberbot.__license__
DESCRIPTION = jabberbot.__doc__

# Extract name and e-mail ("Firstname Lastname <mail@example.org>")
AUTHOR, EMAIL = re.match(r'(.*) <(.*)>', jabberbot.__author__).groups()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as fh:
    LONG_DESCRIPTION = fh.read().strip()

setup(name=PACKAGE,
      version=VERSION,
      description=DESCRIPTION,
      long_decription=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=EMAIL,
      license=LICENSE,
      url=WEBSITE,
      py_modules=MODULES,
      classifiers=['Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Topic :: Software Development'],
      )

