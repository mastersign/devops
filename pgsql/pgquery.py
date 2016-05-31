#!/usr/bin/env python

# Tobias Kiertscher <dev@mastersign.de>

from sys import stdin
import re
import argparse
from getpass import getpass
import psycopg2
import prettytable

def_user = 'postgres'
def_password = ''

supported_formats = ['table', 'csv', 'tsv', 'html', 'md_table', 'md_list']

parser = argparse.ArgumentParser(
    description='running an SQL query against a PostgreSQL database')

parser.add_argument(
    'host',
    help='The name or IP address of the server.')
parser.add_argument(
    'dbname',
    help='The name of the database.')
parser.add_argument(
    '-u', '--user',
    default=def_user,
    help='The username for authentication to the server.')
parser.add_argument(
    '-pw', '--password',
    help='The password for authentication to the server.')
parser.add_argument(
    '-ssl',
    action='store_true',
    help='Activates SSL encryption for the connection.')
parser.add_argument(
    '-o', '--format',
    default='table',
    help='The output format: {0}.'.format(', '.join(supported_formats)))
parser.add_argument(
    '-pq', '--print-query',
    action='store_true',
    help='A switch for activating output of mogrified SQL.')
parser.add_argument(
    '-pc', '--print-connection',
    action='store_true',
    help='A switch for activating output of connection info.')
parser.add_argument(
    '-f', '--file',
    type=argparse.FileType('r'),
    help='A file with a SQL statement to run.')
parser.add_argument(
    '-qa', '--query-arguments',
    nargs='*',
    default=[],
    help='A number of arguments to inject into the SQL statement.\n' +
         'Every argument is given as a key-value-pair: KEY=VALUE.')

cl_args = parser.parse_args()
password = cl_args.password
if not password:
    if cl_args.user == def_user:
        password = def_password
    else:
        if cl_args.file:
            password = getpass('Password: ')
        else:
            print('You must either specify the password ' +
                  'as a command line argument, ' +
                  'or a SQL file as input.')
            exit(1)

if cl_args.format not in supported_formats:
    print(
        'You must use an output format from the following list: ' +
        ', '.join(supported_formats))
    exit(1)


class Column(object):

    def __init__(this, name, col_type):
        this.name = name
        this.type = col_type


def process_result_format(conn, cur):

    def process_column(col):
        name = col.name

        type_cur = conn.cursor()
        type_cur.execute(
            """
            SELECT typname FROM pg_type AS t
            JOIN pg_namespace AS n ON t.typnamespace = n.oid
            WHERE t.oid = %(oid)s
            """,
            {'oid': col.type_code})
        type_name = type_cur.fetchone()[0]
        type_cur.close()

        return Column(name, type_name)

    return map(process_column, cur.description)


def iterate_rows(cur, cache, f):
    row = cur.fetchone()
    while row:
        f(cache, row)
        row = cur.fetchone()


def execute_query(conn, handlers,
                  query, query_params, **nargs):

    if 'mogrify' not in nargs:
        nargs['mogrify'] = False

    cur = conn.cursor()

    if nargs['mogrify']:
        m_query = cur.mogrify(query, query_params).strip()
        handlers['query_handler'](m_query)

    cur.execute(query, query_params)

    columns = process_result_format(conn, cur)
    cache = {}
    handlers['columns_handler'](cache, columns)
    iterate_rows(cur, cache, handlers['row_handler'])
    handlers['finalizer'](cache)

    cur.close()
    conn.commit()


def run_query(host, dbname, user, password, ssl,
              handlers, query, query_params, **nargs):

    if 'info' not in nargs:
        nargs['info'] = False

    if nargs['info']:
        handlers['info_handler']([
                ('server', host),
                ('database', dbname),
            ])

    conn = psycopg2.connect(
        host=host,
        dbname=dbname,
        sslmode=('require' if ssl else 'allow'),
        user=user,
        password=password)

    execute_query(conn, handlers, query, query_params, **nargs)

    conn.close()


def make_unique(columns):
    cache = {}
    res = []
    for col in columns:
        name = col.name
        new_name = col.name
        if name in cache:
            cache[col.name] = cache[col.name] + 1
            new_name = "{}_{}".format(col.name, cache[col.name])
        else:
            cache[col.name] = 1
        res.append(Column(new_name, col.type))
    return res


def load_query(f):
    if f:
        return f.read()
    else:
        return stdin.read()


def is_numeric_type(type_name):
    return \
        type_name == 'int2' or \
        type_name == 'int4' or \
        type_name == 'int8' or \
        type_name == 'float4' or \
        type_name == 'float8'


def table_info_handler(info):
    for (k, v) in info:
        print('{0}: {1}'.format(k, v))
    print('')


def table_query_handler(query):
    print(query)
    print('')


def table_columns_handler(cache, columns):
    columns = make_unique(columns)
    table = prettytable.PrettyTable(map(lambda c: c.name, columns))
    cache['table'] = table
    table.padding_width = 0
    table.border = True
    table.vrules = prettytable.ALL
    table.valign = 't'
    # table.int_format = '8'
    table.float_format = '0.3'
    for c in columns:
        if is_numeric_type(c.type):
            table.align[c.name] = 'r'
        elif c.type == 'bool':
            table.align[c.name] = 'c'
        else:
            table.align[c.name] = 'l'


def table_row_handler(cache, row):
    table = cache['table']
    table.add_row(row)


def table_finalizer(cache):
    table = cache['table']
    print(table)


table_handlers = {
        'info_handler': table_info_handler,
        'query_handler': table_query_handler,
        'columns_handler': table_columns_handler,
        'row_handler': table_row_handler,
        'finalizer': table_finalizer
    }


def escape_csv_value(v, type_name):
    v = str(v)
    if '"' in v:
        v = v.replace('"', '""')
    if '"' in v or ',' in v or \
       type_name == 'text':

        v = '"{0}"'.format(v)

    return v


def csv_info_handler(info):
    for (k, v) in info:
        print('# {0}: {1}'.format(k, v))
    print('')


def csv_query_handler(query):
    line_start_p = re.compile(r'^', re.MULTILINE)
    query = line_start_p.sub('# ', query)
    print(query)
    print('')


def csv_columns_handler(cache, columns):
    cache['columns'] = columns
    print(', '.join(map(
        lambda c: escape_csv_value(c.name, 'text'),
        columns)))


def csv_row_handler(cache, row):
    columns = cache['columns']

    def format_value(v, i):
        return escape_csv_value(v, columns[i].type)

    formatted_row = map(format_value, row, range(len(row)))
    print(', '.join(formatted_row))


def csv_finalizer(cache):
    pass


csv_handlers = {
        'info_handler': csv_info_handler,
        'query_handler': csv_query_handler,
        'columns_handler': csv_columns_handler,
        'row_handler': csv_row_handler,
        'finalizer': csv_finalizer
    }


def escape_tsv_value(v):
    v = str(v)
    v = v.replace("\t", ' ')
    return v


def tsv_info_handler(info):
    for (k, v) in info:
        print('# {0}: {1}'.format(k, v))
    print('')


def tsv_query_handler(query):
    line_start_p = re.compile(r'^', re.MULTILINE)
    query = line_start_p.sub('# ', query)
    print(query)
    print('')


def tsv_columns_handler(cache, columns):
    print("\t".join(map(
        lambda c: escape_tsv_value(c.name),
        columns)))


def tsv_row_handler(cache, row):
    print("\t".join(map(escape_tsv_value, row)))


def tsv_finalizer(cache):
    pass


tsv_handlers = {
        'info_handler': tsv_info_handler,
        'query_handler': tsv_query_handler,
        'columns_handler': tsv_columns_handler,
        'row_handler': tsv_row_handler,
        'finalizer': tsv_finalizer
    }


def html_info_handler(info):
    print('<ul>')
    for (k, v) in info:
        print('  <li>{0}: {1}</li>'.format(k, v))
    print('</ul>')


def html_query_handler(query):
    print('<pre><code class="sql-query">')
    print(query)
    print('</code></pre>')
    print('')


def html_columns_handler(cache, columns):
    columns = make_unique(columns)
    cache['columns'] = columns
    print('<table>')
    print('  <thead><tr>')
    for c in columns:
        print('    <td>' + c.name + '</td>')
    print('  </tr></thead>')


def html_row_handler(cache, row):
    columns = cache['columns']
    print('<tr>')
    for i in range(len(columns)):
        c = columns[i]
        v = str(row[i])
        css_class = None
        if is_numeric_type(c.type):
            css_class = 'number'
        elif c.type == 'bool':
            css_class = 'bool'
        elif c.type == 'timestamp':
            css_class = 'timestamp'
        if css_class:
            print('    <td class="' + css_class + '">' + v + '</td>')
        else:
            print('    <td>' + v + '</td>')
    print('  </tr>')


def html_finalizer(cache):
    print('</table>')


html_handlers = {
        'info_handler': html_info_handler,
        'query_handler': html_query_handler,
        'columns_handler': html_columns_handler,
        'row_handler': html_row_handler,
        'finalizer': html_finalizer
    }


def escape_md_text(text):
    text = str(text)
    text = text.replace('$', "\\$")
    text = text.replace('*', "\\*")
    text = text.replace('__', "\\_\\_")
    return text


def md_info_handler(info):
    for (k, v) in info:
        print('* **{0}**: `{1}`'.format(
            escape_md_text(k),
            escape_md_text(v)))
    print('')


def md_query_handler(query):
    print('~~~')
    print(query)
    print('~~~')
    print('')


def md_table_columns_handler(cache, columns):
    def align_str(col):
        l = len(col.name)
        if is_numeric_type(col.type):
            return ('-' * (l + 1)) + ':'
        if col.type == 'bool':
            return ':' + ('-' * l) + ':'
        return ':' + ('-' * (l + 1))

    print('| {0} |'.format(
        ' | '.join(map(
            lambda c: c.name,
            columns))))
    print('|{0}|'.format(
        '|'.join(map(align_str, columns))))


def md_table_row_handler(cache, row):
    def escape_cell_value(v):
        v = str(v)
        v = escape_md_text(v)
        v = v.replace('|', '&#448;')
        v = v.replace('\n', '<br>')
        return v
    print('|{0}|'.format(
        '|'.join(map(escape_cell_value, row))))


def md_finalizer(cache):
    pass


md_table_handlers = {
        'info_handler': md_info_handler,
        'query_handler': md_query_handler,
        'columns_handler': md_table_columns_handler,
        'row_handler': md_table_row_handler,
        'finalizer': md_finalizer
    }


def md_list_columns_handler(cache, columns):
    cache['columns'] = columns


def md_list_row_handler(cache, row):
    columns = cache['columns']
    if len(row) > 0:
        print('* **{0}**'.format(escape_md_text(row[0])))
    for i in range(len(row)):
        name = escape_md_text(columns[i].name)
        value = str(row[i])
        if "\n" in value:
            print('    + __{0}__:'.format(name))
            print('')
            print('~~~')
            print(value)
            print('~~~')
            print('')
        else:
            value = escape_md_text(value)
            print('    + __{0}__: {1}'.format(name, value))


md_list_handlers = {
        'info_handler': md_info_handler,
        'query_handler': md_query_handler,
        'columns_handler': md_list_columns_handler,
        'row_handler': md_list_row_handler,
        'finalizer': md_finalizer
    }

if cl_args.format == 'csv':
    handlers = csv_handlers
elif cl_args.format == 'tsv':
    handlers = tsv_handlers
elif cl_args.format == 'md_table':
    handlers = md_table_handlers
elif cl_args.format == 'html':
    handlers = html_handlers
elif cl_args.format == 'md_list':
    handlers = md_list_handlers
else:
    handlers = table_handlers


def split_query_arguments(args):
    res = {}
    for (k, v) in map(lambda a: a.split('='), args):
        res[k] = v
    return res

run_query(cl_args.host, cl_args.dbname,
          cl_args.user, password, cl_args.ssl,
          handlers,
          load_query(cl_args.file),
          split_query_arguments(cl_args.query_arguments),
          info=cl_args.print_connection,
          mogrify=cl_args.print_query)
