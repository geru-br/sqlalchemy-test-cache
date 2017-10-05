#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_sqlalchemy_test_cache
----------------------------------

Tests for `sqlalchemy_test_cache` module.
"""
from __future__ import unicode_literals

import collections
import datetime
import json
import unittest

try:
    from unittest import mock
except ImportError:  # PY2
    import mock  # pip install mock...


from sqlalchemy_test_cache.sqlalchemy_test_cache import DumpManager


FakeMetadata = collections.namedtuple('FakeMetadata', 'sorted_tables')
FakeBaseModel = collections.namedtuple('FakeBaseModel', 'metadata')
FakeColumn = collections.namedtuple('FakeColumn', ('name', 'type'))


def fake_render_value(dialect=None, value=None, type_=None):

    if isinstance(value, (datetime.date, datetime.datetime)):
        return repr(value.isoformat())
    return json.dumps(value)


class FakeTable(object):

    def __init__(self, name=None, columns=None):
        self.name = name or 'faketable'
        self.columns = columns or {}

    def __str__(self):
        return 'faketable'


class FakeColumns(collections.OrderedDict):
    @property
    def created(self):
        return 'created'

    @property
    def id(self):
        return 'id'


class DumpManagerTestCase(unittest.TestCase):

    def test_inser_row_template(self):

        expected_template = 'INSERT INTO "{0}" ({1}) VALUES ({2});'

        self.assertEqual(DumpManager.INSERT_ROW_TEMPLATE, expected_template)

    def test_get_table_columns(self):

        columns = collections.OrderedDict((
            ('column1', FakeColumn('colum1', str)),
            ('column2', FakeColumn('colum2', int)),
            ('column3', FakeColumn('colum3', datetime.date)),
            ('column4', FakeColumn('colum4', bool)),
        ))

        table = FakeTable(columns=columns)

        # For this propose, the base model and dbsession should not be necessary
        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        self.assertListEqual(dm._get_table_columns(table), list(columns.values()))

    def test_get_table_columns_name(self):

        columns = collections.OrderedDict((
            ('column1', FakeColumn('colum1', str)),
            ('column2', FakeColumn('colum2', int)),
            ('column3', FakeColumn('colum3', datetime.date)),
            ('column4', FakeColumn('colum4', bool)),
        ))

        table = FakeTable(columns=columns)

        # For this propose, the base model and dbsession should not be necessary
        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        self.assertListEqual(dm._get_table_columns_name(table), list(c.name for c in columns.values()))

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
            FakeColumn('column1', type=bool), FakeColumn('column2', type=int),
            FakeColumn('column3', type=datetime.date), FakeColumn('column4', type=datetime.datetime)
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
            render_value_patched.assert_any_call(mock_dialect, row_value, columns[index].type)

    def test_build_insert_row(self):

        table = FakeTable(columns=collections.OrderedDict((
            ('column1', FakeColumn('column1', type=int)), ('column2', FakeColumn('column2', type=datetime.date))
        )))

        row = 42, datetime.date.today()

        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        with mock.patch.object(dm, '_dump_row_values', return_value=[str(row[0]), row[1].isoformat()]) as dump_row_patched:
            insert_row = dm._build_insert_row(table, row)

        self.assertTrue(dump_row_patched.called)

        self.assertListEqual(dm._get_table_columns_name(table), ['column1', 'column2'])

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

    def test_dump_without_created_or_id(self):

        table = FakeTable(
            name='thespecialone',
            columns=collections.OrderedDict((
                ('name', FakeColumn('name', str)),
                ('age', FakeColumn('age', int)),
                ('updated', FakeColumn('updated', datetime.datetime))
            ))
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
                dm.INSERT_ROW_TEMPLATE.format(
                    table,
                    ', '.join(table.columns),
                    ', '.join(fake_render_value(None, item, None) for item in row)
                )
            )

        self.assertListEqual(result, expected_result)

    def test_dump_with_created(self):

        table = FakeTable(
            name='thespecialone',
            columns=FakeColumns((
                ('name', FakeColumn('name', str)),
                ('age', FakeColumn('age', int)),
                ('created', FakeColumn('created', datetime.datetime))
            ))
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
                patched_order_by = mock.MagicMock()
                patched_order_by.order_by = mock.MagicMock(return_value=rows)
                dbsession_patched.query.return_value = patched_order_by
                result = dm.dump(table)

        patched_order_by.order_by.assert_called_with('created')

        self.assertTrue(mock_render_value.called)
        self.assertEqual(mock_render_value.call_count, 12)  # 4 rows, 3 value per row.

        expected_result = []

        for row in rows:
            expected_result.append(
                dm.INSERT_ROW_TEMPLATE.format(
                    table,
                    ', '.join(table.columns),
                    ', '.join(fake_render_value(None, item, None) for item in row)
                )
            )

        self.assertListEqual(result, expected_result)

    def test_dump_with_id(self):

        table = FakeTable(
            name='thespecialone',
            columns=FakeColumns((
                ('name', FakeColumn('name', str)),
                ('age', FakeColumn('age', int)),
                ('id', FakeColumn('id', int))
            ))
        )

        row1 = 'Name1', 23, 1
        row2 = 'Name2', 24, 2
        row3 = 'Name3', 25, 3
        row4 = 'Name4', 26, 4
        rows = row1, row2, row3, row4

        dm = DumpManager(base_model=mock.Mock(), dbsession=mock.Mock())

        with mock.patch('sqlalchemy_test_cache.sqlalchemy_test_cache.render_value') as mock_render_value:
            mock_render_value.side_effect = fake_render_value

            with mock.patch.object(dm, 'dbsession') as dbsession_patched:
                patched_order_by = mock.MagicMock()
                patched_order_by.order_by = mock.MagicMock(return_value=rows)
                dbsession_patched.query.return_value = patched_order_by
                result = dm.dump(table)

        patched_order_by.order_by.assert_called_with('id')

        self.assertTrue(mock_render_value.called)
        self.assertEqual(mock_render_value.call_count, 12)  # 4 rows, 3 value per row.

        expected_result = []

        for row in rows:
            expected_result.append(
                dm.INSERT_ROW_TEMPLATE.format(
                    table,
                    ', '.join(table.columns),
                    ', '.join(fake_render_value(None, item, None) for item in row)
                )
            )

        self.assertListEqual(result, expected_result)

    def test_dump_all_tables_without_created_or_id(self):

        table1 = FakeTable(
            name='FakeTable1',
            columns=collections.OrderedDict((
                ('name', FakeColumn('name', type=str)),
                ('age', FakeColumn('age', type=int)),
                ('updated', FakeColumn('updated', type=datetime.datetime))
            ))
        )

        table2 = FakeTable(
            name='FakeTable2',
            columns=collections.OrderedDict((
                ('desc', FakeColumn('desc', type=str)),
                ('number', FakeColumn('number', type=int)),
                ('started', FakeColumn('started', type=datetime.datetime))
            ))
        )

        table3 = FakeTable(
            name='FakeTable3',
            columns=collections.OrderedDict((
                ('title', FakeColumn('title', type=str)),
                ('users', FakeColumn('users', type=int)),
                ('updated', FakeColumn('updated', type=datetime.datetime))
            ))
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

                dm.dump_all_tables()

        self.assertTrue(dbsession_patched.query.called)

        self.assertTrue(mock_render_value.called)
        self.assertEqual(mock_render_value.call_count, 9)   # 3 tables, 1 row per table, 3 values per row.

        expected_result = []

        for table in tables:

            expected_result.append(
                dm.INSERT_ROW_TEMPLATE.format(
                    table,
                    ', '.join(table.columns),
                    ', '.join(fake_render_value(None, item, None) for item in rows[table.name][0])
                )
            )

    def test_dump_all_tables_with_created_and_id(self):

        table1 = FakeTable(
            name='FakeTable1',
            columns=FakeColumns((
                ('name', FakeColumn('name', type=str)),
                ('age', FakeColumn('age', type=int)),
                ('created', FakeColumn('created', type=datetime.datetime))
            ))
        )

        table2 = FakeTable(
            name='FakeTable2',
            columns=FakeColumns((
                ('desc', FakeColumn('desc', type=str)),
                ('number', FakeColumn('number', type=int)),
                ('created', FakeColumn('created', type=datetime.datetime))
            ))
        )

        table3 = FakeTable(
            name='FakeTable3',
            columns=FakeColumns((
                ('title', FakeColumn('title', type=str)),
                ('users', FakeColumn('users', type=int)),
                ('id', FakeColumn('id', type=int))
            ))
        )

        rows = {
            'FakeTable1': [('Name1', 42, datetime.datetime.now())],
            'FakeTable2': [('New item', 100, datetime.datetime.now())],
            'FakeTable3': [('The awesome potato', 9001, 1)]
        }

        tables = table1, table2, table3

        fake_base_model = FakeBaseModel(metadata=FakeMetadata(sorted_tables=tables))

        dm = DumpManager(base_model=fake_base_model, dbsession=None)

        with mock.patch('sqlalchemy_test_cache.sqlalchemy_test_cache.render_value') as mock_render_value:

            mock_render_value.side_effect = fake_render_value

            with mock.patch.object(dm, 'dbsession') as dbsession_patched:

                patched_order_by = mock.MagicMock()
                patched_order_by.order_by = mock.MagicMock(side_effect=rows.values())
                dbsession_patched.query.return_value = patched_order_by

                dm.dump_all_tables()

        patched_order_by.order_by.assert_has_calls([mock.call(u'created'), mock.call(u'created'), mock.call(u'id')])

        self.assertTrue(mock_render_value.called)
        self.assertEqual(mock_render_value.call_count, 9)   # 3 tables, 1 row per table, 3 values per row.

        expected_result = []

        for table in tables:

            expected_result.append(
                dm.INSERT_ROW_TEMPLATE.format(
                    table,
                    ', '.join(table.columns),
                    ', '.join(fake_render_value(None, item, None) for item in rows[table.name][0])
                )
            )
