#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_decorator
----------------------------------

Tests for `sqlalchemy_test_cache.decorator` module.
"""
from __future__ import unicode_literals

import unittest
try:
    from unittest import mock
except ImportError:  # python2
    import mock

from sqlalchemy_test_cache.decorator import cache_sql


class FakeDumpManager(object):

    def __init__(self, side_effect):
        self.side_effect = side_effect

    def __call__(self, base_model, dbsession):

        self.base_model = base_model
        self.dbsession = dbsession

        return self.side_effect

    def dump_all_tables(self):
        pass


class DecoratorTestCase(unittest.TestCase):

    @mock.patch('sqlalchemy_test_cache.decorator.generate_dump_path')
    @mock.patch('sqlalchemy_test_cache.decorator.DumpManager')
    @mock.patch('sqlalchemy_test_cache.decorator.os.path.exists')
    @mock.patch('sqlalchemy_test_cache.decorator.load_dump_data_from_file')
    def test_dump_path_using_test_case_name_and_id(self, load_patched, exists_patched, manager_patched, generate_patched):

        generate_patched.return_value = '/tmp/FakeTestCase.dump'

        # In this context, base_model and dbsession won't be used
        base_model, dbsession = None, None

        fake_test_function = mock.Mock()
        fake_test_function.__name__ = 'test_fake'

        decorated_test_case = cache_sql(base_model, dbsession)(fake_test_function)

        self_patched = mock.Mock()
        self_patched.__class__.__name__ = 'FakeTestCase'

        decorated_test_case(self_patched)

        self.assertTrue(generate_patched.called)
        generate_patched.assert_called_once_with('FakeTestCase', id(self_patched.__class__))

        self.assertTrue(exists_patched.called)
        exists_patched.assert_called_once_with('/tmp/FakeTestCase.dump')

    @mock.patch('sqlalchemy_test_cache.decorator.generate_dump_path')
    @mock.patch('sqlalchemy_test_cache.decorator.os.path.exists')
    @mock.patch('sqlalchemy_test_cache.decorator.load_dump_data_from_file')
    @mock.patch('sqlalchemy_test_cache.decorator.DumpManager')
    def test_dump_manager_base_model_and_dbsession(self, dump_manager_patched, *mocks):

        base_model = mock.Mock()
        dbsession = mock.Mock()

        fake_test_function = mock.Mock()
        fake_test_function.__name__ = 'test_fake'

        decorated_test_case = cache_sql(base_model, dbsession)(fake_test_function)

        self_patched = mock.Mock()
        self_patched.__class__.__name__ = 'FakeTestCase'

        decorated_test_case(self_patched)

        self.assertTrue(dump_manager_patched.called)
        dump_manager_patched.assert_called_once_with(base_model, dbsession)

    @mock.patch('sqlalchemy_test_cache.decorator.DumpManager')
    @mock.patch('sqlalchemy_test_cache.decorator.os.path.exists')
    @mock.patch('sqlalchemy_test_cache.decorator.write_dump_data_to_file')
    def test_write_dump_to_file_if_dump_file_does_not_exists(self, write_patched, exists_patched, manager_patched):

        exists_patched.return_value = False

        base_model = mock.Mock()
        dbsession = mock.Mock()

        fake_test_function = mock.Mock()
        fake_test_function.__name__ = 'test_fake'

        decorated_test_case = cache_sql(base_model, dbsession)(fake_test_function)

        self_patched = mock.Mock()
        self_patched.__class__.__name__ = 'FakeTestCase'

        decorated_test_case(self_patched)

        self.assertTrue(fake_test_function.called)
        fake_test_function.assert_called_once_with(self_patched)

        self.assertTrue(write_patched.called)
        write_patched.assert_called_once_with('/tmp/FakeTestCase-{}.dump'.format(id(self_patched.__class__)), '')

    @mock.patch('sqlalchemy_test_cache.decorator.DumpManager')
    @mock.patch('sqlalchemy_test_cache.decorator.os.path.exists')
    @mock.patch('sqlalchemy_test_cache.decorator.load_dump_data_from_file')
    def test_loads_from_file_when_dump_file_exists(self, load_dump_patched, exists_patched, manager_patched):

        load_dump_patched.return_value = ['INSERT INTO "faketable" ...\n']

        exists_patched.return_value = True

        dump_manager_loads_patched = mock.Mock()
        manager_patched.side_effect = FakeDumpManager(side_effect=dump_manager_loads_patched)

        base_model = mock.Mock()
        dbsession = mock.Mock()

        fake_test_function = mock.Mock()
        fake_test_function.__name__ = 'test_fake'

        decorated_test_case = cache_sql(base_model, dbsession)(fake_test_function)

        self_patched = mock.Mock()
        self_patched.__class__.__name__ = 'FakeTestCase'

        decorated_test_case(self_patched)

        self.assertTrue(manager_patched.called)

        self.assertTrue(load_dump_patched.called)
        load_dump_patched.assert_called_once_with('/tmp/FakeTestCase-{}.dump'.format(id(self_patched.__class__)))

        self.assertTrue(dump_manager_loads_patched.loads.called)
        dump_manager_loads_patched.loads.assert_called_once_with(['INSERT INTO "faketable" ...\n'])
