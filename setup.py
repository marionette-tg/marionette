#!/usr/bin/env python
# coding: utf-8

import os

from setuptools import setup

if os.name == 'nt':
    import py2exe

setup(name='marionette-tg',
      console=['bin/marionette_client','bin/marionette_server'],
      scripts=['bin/marionette_client','bin/marionette_server'],
      test_suite='marionette_tg',
      packages=['marionette_tg','marionette_tg.plugins','marionette_tg.executables'],
      package_data={'marionette_tg': ['marionette.conf','formats/*.mar','formats/*.py']},
      zipfile="marionette.zip",
      options={"py2exe": {
          "bundle_files": 2,
          "optimize": 0,
          "compressed": True,
          "includes": [
                       'importlib','twisted','fte','regex2dfa','ply','pycurl',
                       'marionette_tg.plugins._channel',
                       'marionette_tg.plugins._fte',
                       'marionette_tg.plugins._io',
                       'marionette_tg.plugins._model',
                       'marionette_tg.plugins._tg',
                      ],
          "dll_excludes": ["w9xpopen.exe"],
      }
      },
      include_package_data=True,
      install_requires=['importlib','twisted','fte','regex2dfa','ply','pycurl'],
      version='0.0.2',
      description='Marionette',
      long_description='The polymorphic, programmable proxy.',
      author='Kevin P. Dyer',
      author_email='kpdyer@gmail.com',
      url='https://github.com/kpdyer/marionette')
