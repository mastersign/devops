#!/usr/bin/env python

# Tobias Kiertscher <dev@mastersign.de>

from argparse import ArgumentParser
import time
from datetime import datetime
import pika
import traceback

# Process command line arguments

parser = ArgumentParser(
    description='consuming a RabbitMQ queue')

parser.add_argument(
    'queue',
    help='The name of the queue to consume.')
parser.add_argument(
    '-n', '--node',
    dest='host', default='localhost',
    help='A host name or IP address of the RabbitMQ node. Default value is localhost.')
parser.add_argument(
    '-p', '--port',
    default=5672, type=int,
    help='A port for the AMQP service at the RabbitMQ node. Default value is 5672.')
parser.add_argument(
    '-u', '--user',
    dest='username', default='devops',
    help='A username for authentification.')
parser.add_argument(
    '-pw', '--password',
    default='devops',
    help='A password for authentification.')

args = parser.parse_args()

# Establish connection to AMQP server

credentials = pika.credentials.PlainCredentials(
    username=args.username,
    password=args.password,
    erase_on_connect=True)
connectionParams = pika.ConnectionParameters(
    host=args.host,
    port=args.port,
    credentials=credentials)
connection = pika.BlockingConnection(connectionParams)
channel = connection.channel()

# Check for requested queue

result = channel.queue_declare(
    queue=args.queue,
    auto_delete=False,
    exclusive=False,
    passive=True)
queue_name = args.queue


# exract and format timestamp as string
def get_timestamp(properties):
    tsv = properties.timestamp
    if type(tsv) is float:
        ts = datetime.fromtimestamp(tsv)
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
    elif type(tsv) is int:
        ts = datetime.fromtimestamp(float(tsv))
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
    else:
        ts_str = str(tsv)
    return ts_str


# process consumed message
def message_callback(ch, method, properties, body):
    ts_str = get_timestamp(properties)
    print('{} [{}]: {}'.format(ts_str, method.routing_key, body))


# wrap the message processing with exception handling and acknowleding
def ack_callback(ch, method, properties, body):
    try:
        message_callback(ch, method, properties, body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except (Exception) as e:
        print("Error while acknowledging message:")
        print(traceback.format_exc(e))


# start consuming messages

channel.basic_consume(ack_callback, queue_name)

print('Press Ctrl+C to exit ...')
time.sleep(2.0)

try:
    channel.start_consuming()
except (KeyboardInterrupt):
    exit()
