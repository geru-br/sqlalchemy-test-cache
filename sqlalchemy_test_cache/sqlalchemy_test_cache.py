from __future__ import unicode_literals

import logging
import operator
try:
    from functools import reduce
except ImportError:
    pass  # py2

from .utils import render_value


logger = logging.getLogger(__name__)


class DumpManager(object):

    INSERT_ROW_TEMPLATE = 'INSERT INTO "{0}" ({1}) VALUES ({2});'

    def __init__(self, base_model, dbsession):
        self.base_model = base_model
        self.dbsession = dbsession

    def _get_table_columns(self, table):
        return [column for column in table.columns.values()]

    def _get_table_columns_name(self, table):
        return [column.name for column in self._get_table_columns(table)]

    def _get_table_rows(self, table):
        return self.dbsession.query(table)

    def _dump_row_values(self, row, columns):
        return [
            render_value(self.dbsession.bind.dialect, value, columns[i].type) for i, value in enumerate(row)
        ]

    def _build_insert_row(self, table, row):
        return self.INSERT_ROW_TEMPLATE.format(
            table,
            ', '.join(self._get_table_columns_name(table)),
            ', '.join(self._dump_row_values(row, self._get_table_columns(table)))
        )

    @property
    def tables(self):
        return self.base_model.metadata.sorted_tables

    def dump(self, table):

        logger.info('Generating dump for the table: {!r}'.format(table.name))

        return [self._build_insert_row(table, row) for row in self._get_table_rows(table)]

    def dump_all_tables(self):

        logger.info('Starting dump process of {} tables'.format(len(self.tables)))

        return reduce(operator.add, map(self.dump, self.tables))

    def loads(self, content):

        for line in content:
            self.dbsession.execute(line.strip())

        self.dbsession.flush()
