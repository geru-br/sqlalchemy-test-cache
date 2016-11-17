#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_sqlalchemy_test_cache
----------------------------------

Tests for `sqlalchemy_test_cache` module.
"""

import collections
import datetime
import itertools
import json
import unittest

try:
    from unittest import mock
except ImportError:  # PY2
    import mock  # pip install mock...


from sqlalchemy_test_cache.sqlalchemy_test_cache import DumpManager


FakeMetadata = collections.namedtuple('FakeMetadata', 'sorted_tables')
FakeBaseModel = collections.namedtuple('FakeBaseModel', 'metadata')
FakeColumn = collections.namedtuple('FakeColumn', 'type')


def fake_render_value(value=None, dialect=None, type=None):

    if isinstance(value, (datetime.date, datetime.datetime)):
        return repr(value.isoformat())
    return json.dumps(value)


class FakeTable(object):

    def __init__(self, name=None, columns=None):
        self.name = name or 'faketable'
        self.columns = columns or {}

    def __str__(self):
        return 'faketable'


class DumpManagerTestCase(unittest.TestCase):

    def test_inser_row_template(self):

        expected_template = 'INSERT INTO "{0}" ({1}) VALUES ({2});'

        self.assertEqual(DumpManager.INSERT_ROW_TEMPLATE, expected_template)

    def test_get_table_columns(self):

        columns = {
            'colum1': 'colum1_str',
            'colum2': 'colum2_int',
            'colum3': 'colum3_date',
            'colum4': 'colum4_bool',
        }

        table = FakeTable(columns=columns)

        # For this propose, the base model and dbsession should not be necessary
        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        self.assertListEqual(dm._get_table_columns(table), columns.values())

    def test_get_table_columns_name(self):

        columns = {
            'colum1': 'colum1_str',
            'colum2': 'colum2_int',
            'colum3': 'colum3_date',
            'colum4': 'colum4_bool',
        }

        table = FakeTable(columns=columns)

        # For this propose, the base model and dbsession should not be necessary
        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        self.assertListEqual(dm._get_table_columns_name(table), columns.keys())

    def test_get_table_rows(self):

        # Just assert the rows will be retrieved using the dbsession

        table = FakeTable(columns={})

        dm = DumpManager(base_model=mock.Mock(), dbsession=None)

        mock_query = mock.Mock()

        with mock.patch.object(dm, 'dbsession') as dbsession_patched:
            dbsession_patched.query = mock_query

            dm._get_table_rows(table)

        self.assertTrue(mock_query.called)
        mock_query.assert_called_once_with(table)

    @mock.patch('sqlalchemy_test_cache.sqlalchemy_test_cache.render_value')
    def test_dump_row_values(self, render_value_patched):

        # TODO: Assert the return

        columns = [
            FakeColumn(type=bool), FakeColumn(type=int), FakeColumn(type=datetime.date), FakeColumn(type=datetime.datetime)
        ]

        row = True, 42, datetime.date.today(), datetime.datetime.now()

        mock_dialect = mock.PropertyMock()

        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        with mock.patch.object(dm, 'dbsession', new_callable=mock_dialect) as dbsession_patched:
            dbsession_patched.bind.dialect = mock_dialect
            dm._dump_row_values(row, columns)

        self.assertTrue(mock_dialect.called)

        self.assertEqual(render_value_patched.call_count, 4)

        for index, row_value in enumerate(row):
            render_value_patched.assert_any_call(dialect=mock_dialect, type=columns[index].type, value=row_value)

    def test_build_insert_row(self):

        table = FakeTable(
            columns=collections.OrderedDict(column1=FakeColumn(type=int), column2=FakeColumn(type=datetime.date))
        )

        row = 42, datetime.date.today()

        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        with mock.patch.object(dm, '_dump_row_values', return_value=[str(row[0]), row[1].isoformat()]) as dump_row_patched:
            insert_row = dm._build_insert_row(table, row)

        self.assertTrue(dump_row_patched.called)

        expected_insert_row = 'INSERT INTO "faketable" (column1, column2) VALUES ({}, {});'.format(row[0], row[1])

        self.assertEqual(insert_row, expected_insert_row)

    def test_tables(self):

        # The return should use the base_model.metada.sorted_tables

        table1 = FakeTable(name='faketable1')
        table2 = FakeTable(name='faketable2')

        fake_base_model = FakeBaseModel(metadata=FakeMetadata(sorted_tables=[table1, table2]))

        dm = DumpManager(base_model=None, dbsession=mock.Mock())

        with mock.patch.object(dm, 'base_model', new_callable=mock.PropertyMock(return_value=fake_base_model)):
            result = dm.tables

        self.assertListEqual(result, fake_base_model.metadata.sorted_tables)

    def test_dump(self):

        table = FakeTable(
            name='thespecialone',
            columns=collections.OrderedDict(
                name=FakeColumn(type=str),
                age=FakeColumn(type=int),
                created=FakeColumn(type=datetime.datetime)
            )
        )

        row1 = 'Name1', 23, datetime.datetime.now()
        row2 = 'Name2', 24, datetime.datetime.now()
        row3 = 'Name3', 25, datetime.datetime.now()
        row4 = 'Name4', 26, datetime.datetime.now()
        rows = row1, row2, row3, row4

        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        with mock.patch('sqlalchemy_test_cache.sqlalchemy_test_cache.render_value') as mock_render_value:

            mock_render_value.side_effect = fake_render_value

            with mock.patch.object(dm, 'dbsession') as dbsession_patched:

                dbsession_patched.query.return_value = rows
                result = dm.dump(table)

        self.assertTrue(dbsession_patched.query.called)

        self.assertTrue(mock_render_value.called)
        self.assertEqual(mock_render_value.call_count, 12)  # 4 rows, 3 value per row.

        expected_result = []

        for row in rows:

            expected_result.append(
                dm.INSERT_ROW_TEMPLATE.format(table, ', '.join(table.columns), ', '.join(map(fake_render_value, row)))
            )

        self.assertListEqual(result, expected_result)

    def test_dump_all_tables(self):

        table1 = FakeTable(
            name='FakeTable1',
            columns=collections.OrderedDict(
                name=FakeColumn(type=str),
                age=FakeColumn(type=int),
                created=FakeColumn(type=datetime.datetime)
            )
        )

        table2 = FakeTable(
            name='FakeTable2',
            columns=collections.OrderedDict(
                desc=FakeColumn(type=str),
                number=FakeColumn(type=int),
                started=FakeColumn(type=datetime.datetime)
            )
        )

        table3 = FakeTable(
            name='FakeTable3',
            columns=collections.OrderedDict(
                title=FakeColumn(type=str),
                users=FakeColumn(type=int),
                created=FakeColumn(type=datetime.datetime)
            )
        )

        rows = {
            'FakeTable1': [('Name1', 42, datetime.datetime.now())],
            'FakeTable2': [('New item', 100, datetime.datetime.now())],
            'FakeTable3': [('The awesome potato', 9001, datetime.datetime.now())]
        }

        tables = table1, table2, table3

        fake_base_model = FakeBaseModel(metadata=FakeMetadata(sorted_tables=tables))

        dm = DumpManager(base_model=fake_base_model, dbsession=None)

        with mock.patch('sqlalchemy_test_cache.sqlalchemy_test_cache.render_value') as mock_render_value:

            mock_render_value.side_effect = fake_render_value

            with mock.patch.object(dm, 'dbsession') as dbsession_patched:

                dbsession_patched.query.side_effect = lambda table: rows[table.name]

                result = dm.dump_all_tables()

        self.assertTrue(dbsession_patched.query.called)

        self.assertTrue(mock_render_value.called)
        self.assertEqual(mock_render_value.call_count, 9)   # 3 tables, 1 row per table, 3 values per row.

        expected_result = []

        for table in tables:

            expected_result.append(
                dm.INSERT_ROW_TEMPLATE.format(
                    table,
                    ', '.join(table.columns),
                    ', '.join(map(fake_render_value, rows[table.name][0]))  # index 0 because there is only one row per table
                )
            )

        self.assertListEqual(result, expected_result)

    def test_loads(self):

        dm = DumpManager(base_model=None, dbsession=None)

        with mock.patch.object(dm, 'dbsession') as dbsession_patched:

            dm.loads(["INSERT INTO ..."])

        self.assertTrue(dbsession_patched.execute.called)

        dbsession_patched.execute.assert_called_once_with("INSERT INTO ...")
