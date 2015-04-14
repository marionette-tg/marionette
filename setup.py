#!/usr/bin/env python

from setuptools import setup
from setuptools import Extension
from setuptools.command.build_py import build_py as DistutilsBuild
from setuptools.command.install import install as DistutilsInstall

setup(name='marionette',
      install_requires=['fte'],
      test_suite='marionette',
      version='alpha',
      description='Marionette',
      long_description='The polymorphic, programmable proxy.',
      author='Kevin P. Dyer',
      author_email='kpdyer@gmail.com',
      url='https://github.com/kpdyer/marionette', )
