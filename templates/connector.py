__doc__ = """connector.py

Subscribe to relevant topics from RMQ channel and publish results

"""
import argparse
from datetime import date, datetime
import os
from pathlib import Path
import json
import sys
import typing
from typing import Literal, Iterable

import pika

InputTopic = Literal[{{INPUT_TOPICS}}]
OutputTopic = Literal[{{OUTPUT_TOPICS}}]


def json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class Consumer:
    def __init__(self, args, callback):
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=args.rabbitmq_host)
        )
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=args.rabbitmq_exchange, exchange_type="direct"
        )

        self._result = self._channel.queue_declare("", exclusive=True)
        self._queue_name = self._result.method.queue

        topics: Iterable[InputTopic] = typing.get_args(InputTopic)
        print(topics)
        for topic in topics:
            self._channel.queue_bind(
                exchange=args.rabbitmq_exchange,
                queue=self._queue_name,
                routing_key=topic,
            )

        def _callback(ch, method, properties, body):
            try:
                callback(ch, method, properties, body)
            except Exception as ex:
                print(f" [!] unhandled exception: {ex}")

        self._channel.basic_consume(
            queue=self._queue_name,
            on_message_callback=_callback if callback else self._default_callback,
            auto_ack=True,
        )

    def _default_callback(self, ch, method, properties, body) -> None:
        try:
            print(" [default] %r:%r" % (method.routing_key, body))
        except Exception as ex:
            print(f" [!] unhandled exception: {ex}")

    def start_consuming(self) -> None:
        self._channel.start_consuming()


class Producer:
    def __init__(self, args):
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=args.rabbitmq_host)
        )
        self._channel = self._connection.channel()
        self._exchange = args.rabbitmq_exchange
        self._channel.exchange_declare(exchange=self._exchange, exchange_type="direct")

    def publish(self, message: dict, topic: OutputTopic) -> None:
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key=topic,
            body=json.dumps(message, default=json_serialize),
        )

    def close(self) -> None:
        self._connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="Connector for Captini module.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--rabbitmq-exchange", type=str, default="captini")
    parser.add_argument("--rabbitmq-host", type=str, default="rabbitmq")
    args = parser.parse_args()

    producer = Producer(args)

    def callback(ch, method, properties, body) -> None:
        {{HANDLE_INPUT_TOPICS_AND_PUBLISH_OUTPUT}}

    consumer = Consumer(args, callback=callback)
    consumer.start_consuming()


if __name__ == "__main__":
    main()
