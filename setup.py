#!/usr/bin/env python3
# coding: utf-8

from setuptools import setup, find_packages

with open("PYPI_README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='marionette-tg',
    version='0.2.0',
    description='Marionette - The polymorphic, programmable proxy.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Kevin P. Dyer',
    author_email='kpdyer@gmail.com',
    url='https://github.com/marionette-tg/marionette',
    license='MIT',
    scripts=['bin/marionette_client', 'bin/marionette_server'],
    packages=find_packages(),
    package_data={'marionette': ['marionette.conf', 'formats/*.mar', 'formats/**/*.mar', 'formats/**/**/*.mar']},
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        'twisted>=25.5.0',
        'fte>=0.2.1',
        'ply>=3.11',
        'requests>=2.28.0',
        'PySocks>=1.7.0',
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
