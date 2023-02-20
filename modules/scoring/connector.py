__doc__ = """connector.py

Subscribe to relevant topics from RMQ channel and publish results

"""
# TODO(rkjaran): Create a template for connector code, to be used for generating this
#   file.
import argparse
from datetime import date, datetime
import os
from pathlib import Path
import json
import sys
import typing
from typing import Literal, Iterable

import pika

InputTopic = Literal["PRONUNCIATION_SCORE", "PRONUNCIATION_ALIGNMENT", "PROSODY_SCORE"]
OutputTopic = Literal["SCORING_FEEDBACK"]


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
        # TODO(rkjaran): probably shouldn't have separate connections for consumer and
        #   producer. Who knows?
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
        description="Connector for Captini scoring module.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--rabbitmq-exchange", type=str, default="captini")
    parser.add_argument("--rabbitmq-host", type=str, default="rabbitmq")
    args = parser.parse_args()

    producer = Producer(args)

    def callback(ch, method, properties, body) -> None:
        # TODO(rkjaran): Implement some kind of combining queue for waiting for multiple
        #   messages for a single output message.
        if (
            method.routing_key == "PRONUNCIATION_ALIGNMENT"
        ):  # and also "PRONUNCIATION_SCORE" and "PROSODY_SCORE"
            msg = json.loads(body)
            session_id = msg.get("session_id", "UNKNOWN_SESSION")
            text_id = msg["text_id"]
            speaker_id = msg["speaker_id"]

            producer.publish(
                {
                    "timestamp": datetime.now(),
                    "session_id": session_id,
                    "speaker_id": speaker_id,
                    "text_id": text_id,
                    "score": -1.0,  # TODO(rkjaran): Get from PRONUNCIATION_SCORE
                    "prosody": None,  # TODO(rkjaran): Get from PROSODY_SCORE
                    "alignment": msg["alignment"],
                },
                "SCORING_FEEDBACK",
            )

    consumer = Consumer(args, callback=callback)
    consumer.start_consuming()


if __name__ == "__main__":
    main()
