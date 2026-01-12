#!/usr/bin/env python3
# coding: utf-8

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='marionette-tg',
    version='0.1.0',
    description='Marionette - The polymorphic, programmable proxy.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Kevin P. Dyer',
    author_email='kpdyer@gmail.com',
    url='https://github.com/marionette-tg/marionette',
    license='MIT',
    scripts=['bin/marionette_client', 'bin/marionette_server'],
    packages=find_packages(),
    package_data={'marionette_tg': ['marionette.conf', 'formats/*.mar', 'formats/**/*.mar', 'formats/**/**/*.mar']},
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        'twisted>=21.0.0',
        'fte>=0.1.0',
        'regex2dfa>=0.1.9',
        'ply>=3.11',
        'pycurl>=7.43.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: Proxy Servers',
        'Topic :: Security',
    ],
)
