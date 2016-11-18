from __future__ import unicode_literals

import json
import tempfile
from datetime import date, timedelta, datetime


try:
    basestring
except NameError:
    basestring = str
    long = int


def generate_value_literal_compiler(dialect):

    class ValueLiteralCompiler(dialect.statement_compiler):

        def visit_bindparam(self, bindparam, within_columns_clause=False,
                            literal_binds=False, **kwargs):
            return self.render_literal_value(bindparam.value, bindparam.type)

        def render_array_value(self, val, item_type):
            if isinstance(val, list):
                return "{%s}" % ",".join([self.render_array_value(x, item_type) for x in val])
            return self.render_literal_value(val, item_type)

        def render_literal_value(self, value, type_):

            if value is None:
                return 'Null'
            elif isinstance(value, long):
                return str(value)
            elif isinstance(value, (basestring, date, datetime, timedelta)):
                return "'%s'" % str(value).replace("'", "''")
            elif isinstance(value, list):
                return "'{%s}'" % (",".join([self.render_array_value(x, type_.item_type) for x in value]))
            elif isinstance(value, dict):
                return "'%s'" % json.dumps(value)

            return super(ValueLiteralCompiler, self).render_literal_value(value, type_)

    return ValueLiteralCompiler


def generate_dump_path(class_name, class_id, use_tmp=True, basedir=None):

    if basedir and use_tmp:
        raise ValueError(
            'To use the basedir {!r}, you must set the parameter {!r} as {!r}.'.format(
                '/home/alexandre', 'use_tmp', False
            )
        )

    if not use_tmp and not basedir:
        raise ValueError('As the parameter {!r} is {!r}, you need to inform a basedir'.format(
            'use_tmp', False
        ))

    return '{}/{}-{}.dump'.format(basedir or tempfile.gettempdir(), class_name, class_id)


def load_dump_data_from_file(dump_file_path):

    with open(dump_file_path) as f:

        while True:

            data = f.readline()

            if not data:
                break

            else:
                yield data


def write_dump_data_to_file(dump_file_path, dump_data):
    with open(dump_file_path, 'w') as f:
        f.write(dump_data)


def render_value(dialect, type_, value):
    return generate_value_literal_compiler(dialect)(dialect, None).render_literal_value(type_, value)
