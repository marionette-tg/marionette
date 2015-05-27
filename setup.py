#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(name='marionette-tg',
      scripts=['bin/marionette_client','bin/marionette_server'],
      test_suite='marionette_tg',
      packages=['marionette_tg','marionette_tg.plugins'],
      package_data={'marionette_tg': ['marionette.conf','formats/*.mar']},
      include_package_data=True,
      install_requires=['importlib','twisted','fte','regex2dfa','ply'],
      version='0.0.1-7',
      description='Marionette',
      long_description='The polymorphic, programmable proxy.',
      author='Kevin P. Dyer',
      author_email='kpdyer@gmail.com',
      url='https://github.com/kpdyer/marionette')
