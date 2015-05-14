#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(name='marionette',
      scripts=['bin/marionette_client','bin/marionette_server'],
      test_suite='marionette',
      packages=['marionette','marionette.plugins'],
      package_data={'marionette': ['formats/*.mar']},
      include_package_data=True,
      version='0.0.1',
      description='Marionette',
      long_description='The polymorphic, programmable proxy.',
      author='Kevin P. Dyer',
      author_email='kpdyer@gmail.com',
      url='https://github.com/kpdyer/marionette')
