from __future__ import unicode_literals

import json
import tempfile
from datetime import date, timedelta, datetime

from sqlalchemy.orm import Query


try:
    basestring
except NameError:
    basestring = str


def generate_dump_path(class_name, class_id, use_tmp=True, basedir=None):

    if use_tmp:
        basedir = tempfile.gettempdir()

    return '{}/{}-{}.dump'.format(basedir, class_name, class_id)


def render_query(statement, dialect=None, reindent=True):

    if isinstance(statement, Query):
        if dialect is None:
            dialect = statement.session.bind.dialect
        statement = statement.statement
    elif dialect is None:
        dialect = statement.bind.dialect

    class LiteralCompiler(dialect.statement_compiler):

        def visit_bindparam(self, bindparam, within_columns_clause=False,
                            literal_binds=False, **kwargs):
            return self.render_literal_value(bindparam.value, bindparam.type)

        def render_array_value(self, val, item_type):
            if isinstance(val, list):
                return "{%s}" % ",".join([self.render_array_value(x, item_type) for x in val])
            return self.render_literal_value(val, item_type)

        def render_literal_value(self, value, type_):
            if isinstance(value, long):
                return str(value)
            elif isinstance(value, (basestring, date, datetime, timedelta)):
                return "'%s'" % str(value).replace("'", "''")
            elif isinstance(value, list):
                return "'{%s}'" % (",".join([self.render_array_value(x, type_.item_type) for x in value]))
            return super(LiteralCompiler, self).render_literal_value(value, type_)

    return LiteralCompiler(dialect, statement).process(statement)


def render_value(dialect, type_, value):

    class LiteralCompiler(dialect.statement_compiler):

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

            return super(LiteralCompiler, self).render_literal_value(value, type_)

    return LiteralCompiler(dialect, None).render_literal_value(type_, value)
