# Import necessary libraries
import argparse
from datetime import date, datetime
import os
from pathlib import Path
import json
import sys
import typing
from typing import Literal, Iterable
import pika
import psycopg2  # Import PostgreSQL library
from dotenv import load_dotenv, find_dotenv
import asyncio
import websockets
import queue
load_dotenv(find_dotenv())
# Define literals for topic names
InputTopic = Literal[ "PRONUNCIATION_ALIGNMENT"]
OutputTopic = Literal["PRONUNCIATION_SCORE"]
WEB_SOCKET = os.environ['WEB_SOCKET']
async def send_message(message):
    async with websockets.connect(WEB_SOCKET) as websocket:
        await websocket.send(json.dumps(message))

# Define a JSON serializer for non-serializable objects
def json_serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))
# Define a Consumer class for consuming messages
class Consumer:
    def __init__(self, args, callback):
        # Establish a connection to RabbitMQ
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='connector_rabbitmq_1')
        )
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange='captini', exchange_type="direct"
        )

        # Declare a queue and bind it to relevant topics
        self._result = self._channel.queue_declare("", exclusive=True)
        self._queue_name = self._result.method.queue

        topics: Iterable[InputTopic] = typing.get_args(InputTopic)
        for topic in topics:
            self._channel.queue_bind(
                exchange=args.rabbitmq_exchange,
                queue=self._queue_name,
                routing_key=topic,
            )

        # Define the message callback function
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

# Define a Producer class (not used in this example)
class Producer:
    def __init__(self, args):
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='connector_rabbitmq_1')
        )
        self._channel = self._connection.channel()
        self._exchange = args.rabbitmq_exchange
        self._channel.exchange_declare(exchange='captini', exchange_type="direct")

    def publish(self, message: dict, topic: OutputTopic) -> None:
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key=topic,
            body=json.dumps(message, default=json_serialize),
        )

    def close(self) -> None:
        self._connection.close()

# Define the main function
def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Connector for Captini feedback module.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--rabbitmq-exchange", type=str, default="captini")
    parser.add_argument("--rabbitmq-host", type=str, default="connector_rabbitmq_1")
    args = parser.parse_args()

    # Establish a connection to the PostgreSQL database
    try:
        conn = psycopg2.connect(
            dbname='captini',
            user='django',
            password='django',
            host='connector_db_1',
            #port= '5432',
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f'Error connecting to the database: {e}')

    # Define the callback function for processing messages
    def callback(ch, method, properties, body) -> None:
        try:
            response_data = json.loads(body)
            recording_id = response_data["recording_id"]
            score = response_data["score"]["task_feedback"]
            user_id = response_data["speaker_id"]
            task_id = response_data["text_id"]
            feedback = response_data["score"]
            # Update the UserTaskRecording with the received score in the database
            update_query = """
                UPDATE captini_usertaskrecording captni_usertaskrecording
                SET score = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (score, recording_id))
            conn.commit()
            # Update UserTaskScoreStats
            stats_query = """
                INSERT INTO captini_usertaskscorestats (user_id, task_id, score_mean, number_tries)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, task_id)
                DO UPDATE SET
                score_mean = (captini_usertaskscorestats.score_mean * captini_usertaskscorestats.number_tries + %s) / (captini_usertaskscorestats.number_tries + 1),
                number_tries = captini_usertaskscorestats.number_tries + 1
            """
            cursor.execute(stats_query, (user_id, task_id, score, 1, score))
            conn.commit()
            # update user total score
            update_query = """
                UPDATE account_user
                SET score = (
                    SELECT COALESCE(SUM(score_mean), 0)
                    FROM captini_usertaskscorestats
                    WHERE user_id = %s
                )
                WHERE id = %s
            """
            cursor.execute(update_query, (user_id, user_id))
            conn.commit()
            # Send the score data via WebSocket to the frontend
            score_data = {
            "user_id" :user_id,
            "task_id" : task_id,
            "recording_id": recording_id,
            "feedback": feedback,  # Add your feedback message here
            }
            asyncio.get_event_loop().run_until_complete(send_message(score_data))
        except Exception as e:
            print(f'Error in consumeFromQueue callback: {e}')
    consumer = Consumer(args, callback=callback)
    consumer.start_consuming()
    # Close the database connection when done
    cursor.close()
    conn.close()

# Entry point of the script
if __name__ == "__main__":
    main()
