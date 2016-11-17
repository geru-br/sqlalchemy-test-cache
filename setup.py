#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='sqlalchemy_test_cache',
    version='0.1.0',
    description="A way to cache previous query in order to improve performance of complex tests.", # noqa
    long_description=readme + '\n\n' + history,
    author="Geru",
    author_email='dev-oss@geru.com.br',
    url='https://github.com/geru-br/sqlalchemy-test-cache',
    packages=[
        'sqlalchemy_test_cache',
    ],
    package_dir={'sqlalchemy_test_cache':
                 'sqlalchemy_test_cache'},
    entry_points={},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='sqlalchemy-test-cache',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
