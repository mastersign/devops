DevOps Support Scripts
======================

This project contains Python and Shell scripts for devops tasks.

To install the scripts in `~/bin` run `./setup` to create symbolic links to the scripts.

# Commands

* `mysqldump`
  Creates a dump of all tables in a MySQL database as SQL and CSV files.
* `pgquery`
  Queries a PostgreSQL database and prints the result in one of the following formats:
  `table`, `csv`, `tsv`, `html`, `md_table`, `md_list`.
  Use `pgquery -h` to display the usage of the command.
* `mq`
  Consume a RabbitMQ queue and show the messages on the console.
  Use `mq -h` to display the usage of the command.
* `mqtopic`
  Consumes a temporary queue to listen to a RabbitMQ exchange.
  Use `mqtopic -h` to display the usage of the command.

# License

MIT

# `mysqldump`

```
usage: mysqldump.py [-h] [-s SERVER] [-p PORT] [-u USER] [-pw PASSWORD]
                     [-db DATABASE] [-t TARGET]

creating a MySQL dump for a whole schema as SQL file and CSV files

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        The name or IP address of the MySQL server.
  -p PORT, --port PORT  The port to connect to.
  -u USER, --user USER  The username for the login.
  -pw PASSWORD, --password PASSWORD
                        The password for the login.
  -db DATABASE, --database DATABASE
                        The database or schema to dump.
  -t TARGET, --target TARGET
                        The target directory, to store the result files.
```

# `pgquery`

```
usage: pgquery.py [-h] [-u USER] [-pw PASSWORD] [-ssl] [-o FORMAT] [-pq] [-pc]
                  [-f FILE] [-qa [QUERY_ARGUMENTS [QUERY_ARGUMENTS ...]]]
                  host dbname

running an SQL query against a PostgreSQL database

positional arguments:
  host                  The name or IP address of the server.
  dbname                The name of the database.

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  The username for authentication to the server.
  -pw PASSWORD, --password PASSWORD
                        The password for authentication to the server.
  -ssl                  Activates SSL encryption for the connection.
  -o FORMAT, --format FORMAT
                        The output format: table, csv, tsv, html, md_table,
                        md_list.
  -pq, --print-query    A switch for activating output of mogrified SQL.
  -pc, --print-connection
                        A switch for activating output of connection info.
  -f FILE, --file FILE  A file with a SQL statement to run.
  -qa [QUERY_ARGUMENTS [QUERY_ARGUMENTS ...]], --query-arguments [QUERY_ARGUMENTS [QUERY_ARGUMENTS ...]]
                        A number of arguments to inject into the SQL
                        statement. Every argument is given as a key-value-
                        pair: KEY=VALUE.
```

# `mq`

```
usage: mq.py [-h] [-n HOST] [-p PORT] [-u USERNAME] [-pw PASSWORD] queue

consuming a RabbitMQ queue

positional arguments:
  queue                 The name of the queue to consume.

optional arguments:
  -h, --help            show this help message and exit
  -n HOST, --node HOST  A host name or IP address of the RabbitMQ node.
                        Default value is localhost.
  -p PORT, --port PORT  A port for the AMQP service at the RabbitMQ node.
                        Default value is 5672.
  -u USERNAME, --user USERNAME
                        A username for authentification.
  -pw PASSWORD, --password PASSWORD
                        A password for authentification.
```

# `mqtopic`

```
usage: mqtopic.py [-h] [-n HOST] [-p PORT] [-u USERNAME] [-pw PASSWORD]
                  exchange [routing_key]

listen to a RabbitMQ topic exchange

positional arguments:
  exchange              The name of the exchange to listen to.
  routing_key           An optional routing key which is used to create the
                        binding. Default value is #.

optional arguments:
  -h, --help            show this help message and exit
  -n HOST, --node HOST  A host name or IP address of the RabbitMQ node.
                        Default value is localhost.
  -p PORT, --port PORT  A port for the AMQP service at the RabbitMQ node.
                        Default value is 5672.
  -u USERNAME, --user USERNAME
                        A username for authentification.
  -pw PASSWORD, --password PASSWORD
                        A password for authentification.
```
