# -*- coding: utf-8 -*-
"""
    setup

    API for teambox

    :copyright: (c) 2011 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from setuptools import setup

import api


setup(
    name = 'Teambox Client',
    version = api.__version__,
    description = __doc__,

    author = 'Openlabs Technologies & Consulting (P) Limited',
    website = 'http://openlabs.co.in/',
    email = 'info@openlabs.co.in',

    install_requires = [
        'distribute',
    ],

    packages = [
        'teambox',
    ],
    package_dir = {
        'teambox': 'api'    
    }
)
