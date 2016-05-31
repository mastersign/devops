DevOps Support Scripts
======================

This project contains Python and Shell scripts for devops tasks.

To install the scripts in `~/bin` run `./setup` to create symbolic links to the scripts.

Commands
--------

* `mq`
  Consume a RabbitMQ queue and show the messages on the console.
  Use `mq -h` to display the usage of the command.
* `mqtopic`
  Consumes a temporary queue to listen to a RabbitMQ exchange.
  Use `mqtopic -h` to display the usage of the command.
* `pgquery`
  Queries a PostgreSQL database and prints the result in one of the following formats:
  `table`, `csv`, `tsv`, `html`, `md_table`, `md_list`.
  Use `pgquery -h` to display the usage of the command.

