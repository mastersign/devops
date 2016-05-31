#!/usr/bin/env python

# Tobias Kiertscher <dev@mastersign.de>

import pymysql
from os import path
from numbers import Number
import datetime
import locale
import argparse
from getpass import getpass

parser = argparse.ArgumentParser(
    description='creating a MySQL dump for a whole schema as SQL file and CSV files')
parser.add_argument(
    '-s', '--server',
    default='localhost',
    help='The name or IP address of the MySQL server.')
parser.add_argument(
    '-p', '--port',
    default=3306,
    type=int,
    help='The port to connect to.')
parser.add_argument(
    '-u', '--user',
    default='root',
    help='The username for the login.')
parser.add_argument(
    '-pw', '--password',
    help='The password for the login.')
parser.add_argument(
    '-db', '--database',
    help='The database or schema to dump.')
parser.add_argument(
    '-t', '--target',
    default=path.join(path.dirname(__file__), "data"),
    help='The target directory, to store the result files.')
args = parser.parse_args()

db_host = args.server
db_user = args.user
db_passwd = args.password
db_name = args.database
target = args.target
if not db_passwd:
    db_passwd = getpass('Password: ')

if not db_name:
    con = pymysql.connect(host=db_host, user=db_user, passwd=db_passwd)
    cur = con.cursor()
    cur.execute("SHOW SCHEMAS;")
    print("Available schemas:")
    for row in cur.fetchall():
        print(" - " + row[0])
    cur.close()
    con.close()
    exit()

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

con = pymysql.connect(host=db_host, user=db_user, passwd=db_passwd, db=db_name)
cur = con.cursor()

sep = ','

def format_value(v):
    global sep
    if isinstance(v, Number):
        return str(v)
    else:
        v = str(v)
        if sep in v or ' ' in v or '\t' in v:
            return '"' + v.replace('"', '""') + '"'
        else:
            return v

cur.execute("SHOW TABLES")
data = ""
tables = []
for table in cur.fetchall():
    tables.append(table[0])

for table in tables:
    table_csv = ""
    data += "DROP TABLE IF EXISTS `" + str(table) + "`;"

    cur.execute("SHOW CREATE TABLE `" + str(table) + "`;")
    data += "\n" + str(cur.fetchone()[1]) + ";\n\n"

    cur.execute(
        "SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` " +
        "WHERE `TABLE_SCHEMA`='" + db_name + "' " +
        "AND `TABLE_NAME`='" + str(table) + "';")
    columns = []
    for col in cur.fetchall():
        columns.append(str(col[0]))
    table_csv = sep.join(map(format_value, columns)) + "\n"

    cur.execute("SELECT * FROM `" + str(table) + "`;")
    for row in cur.fetchall():
        table_csv += sep.join(map(format_value, row)) + "\n"
        data += "INSERT INTO `" + str(table) + "` VALUES(" + \
                ', '.join(map(lambda v: '"' + str(v) + '"', row)) + ");\n"
    data += "\n\n"

    filename = path.join(target, "table_" + timestamp + "_" + str(table) + ".csv")
    fh = open(filename, "w")
    fh.write(table_csv)
    fh.close()

cur.close()
con.close()

filename = path.join(target, "backup_" + timestamp + ".sql")
fh = open(filename, "w")
fh.write(data)
fh.close()
