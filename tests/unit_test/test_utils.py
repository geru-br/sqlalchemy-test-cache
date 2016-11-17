#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_utils
----------------------------------

Tests for `sqlalchemy_test_cache.utils` module.
"""
from __future__ import unicode_literals

import collections
import contextlib
import os
import tempfile
import unittest
try:
    from unittest import mock
except ImportError:  # python2
    import mock

from sqlalchemy_test_cache import utils


FakeDialect = collections.namedtuple('FakeDialect', 'statement_compiler')
FakeStatementCompiler = collections.namedtuple('FakeStatementCompiler', '')


@contextlib.contextmanager
def create_tmp_file(content, name):

    _tempfile = '{}/{}'.format(tempfile.gettempdir(), name)

    try:
        with open(_tempfile, 'w') as f:
            f.write(content)

        yield
    finally:
        os.unlink(_tempfile)


class GenerateValueLiteralCompilerTestCase(unittest.TestCase):

    def test_ensure_compiler_uses_dialect_statement_compiler(self):

        dialect = FakeDialect(statement_compiler=FakeStatementCompiler)

        qlc = utils.generate_value_literal_compiler(dialect)

        self.assertTrue(issubclass(qlc, FakeStatementCompiler))


class GenerateDumpPathTestCase(unittest.TestCase):

    def test_generate_path_with_default_base_dir(self):

        dump_path = utils.generate_dump_path('ClassName', 123456789)

        basedir = tempfile.gettempdir()

        self.assertEqual('{}/ClassName-123456789.dump'.format(basedir), dump_path)

    def test_exception_when_basedir_is_not_none_but_use_tmp_is_true(self):

        with self.assertRaises(ValueError) as cm:
            utils.generate_dump_path('ClassName', 123456789, use_tmp=True, basedir='/base/dir')

        exception = cm.exception

        expected_message = 'To use the basedir {!r}, you must set the parameter {!r} as {!r}.'.format(
            '/home/alexandre', 'use_tmp', False
        )

        self.assertEqual(str(exception), expected_message)

    def test_exception_when_use_tmp_is_false_but_basedir_is_none(self):

        with self.assertRaises(ValueError) as cm:
            utils.generate_dump_path('ClassName', 123456789, use_tmp=False)

        exception = cm.exception

        expected_message = 'As the parameter {!r} is {!r}, you need to inform a basedir'.format(
            'use_tmp', False
        )

        self.assertEqual(str(exception), expected_message)

    def test_generate_path_when_basedir_is_not_none(self):

        dump_path = utils.generate_dump_path('ClassName', 123456789, use_tmp=False, basedir='/foobar')

        self.assertEqual(dump_path, '/foobar/ClassName-123456789.dump')


class LoadDumpDataFromFileTestCase(unittest.TestCase):

    def test_exception_when_dump_file_path_does_not_exists(self):

        with self.assertRaises(IOError) as cm:
            list(utils.load_dump_data_from_file('foobarbleh'))

        exception = cm.exception

        expected_message = '[Errno 2] No such file or directory: {!r}'.format('foobarbleh')

        self.assertEqual(expected_message, str(exception))

    def test_load_data(self):

        with create_tmp_file(content='INSERT INTO...\n', name='ClassName-123456789.dump'):

            dump_data = list(utils.load_dump_data_from_file('/tmp/ClassName-123456789.dump'))

            self.assertListEqual(['INSERT INTO...\n'], dump_data)


class WriteDumpToFileTestCase(unittest.TestCase):

    def wite_dump_data(self):

        dump_data = '\n'.join(['INSERT INTO "" ...', 'INSERT INTO "" ...', 'INSERT INTO "" ...'])

        dump_file_path = tempfile.NamedTemporaryFile().name

        utils.write_dump_data_to_file(dump_file_path, dump_data)

        self.assertListEqual(
            list(line.strip() for line in utils.load_dump_data_from_file(dump_file_path)),
            dump_data.split('\n')
        )
