import pika
import asyncio
import threading
import os
import json 
from typing import Dict, Any

class RabbitMQClient:
    def __init__(self):
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST")
        self.rabbitmq_username = os.getenv("RABBITMQ_USERNAME")
        self.rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
        self.event_queue_name = os.getenv("RABBITMQ_EVENT_QUEUE_NAME")

    def _connect(self):
        credentials = pika.PlainCredentials(self.rabbitmq_username, self.rabbitmq_password)
        return pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host, credentials=credentials))
    
    def declare_queue(self, queue_name):
        connection = self._connect()
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        connection.close()

    def send(self, queue_name, data):
        connection = self._connect()
        channel = connection.channel()
        # Ensure data is a byte string
        if not isinstance(data, bytes):
            data = json.dumps(data).encode()
        channel.basic_publish(exchange="", routing_key=queue_name, body=data)
        print(" [x] Sent Message")
        connection.close()

    def watch(self, queue_name, search_criteria):
        connection = self._connect()
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        future = asyncio.Future()

        def check_message(ch, method, properties, body):
            message_data = json.loads(body)
            if all(message_data.get(k) == v for k, v in search_criteria.items()):
                if not future.done():
                    future.set_result(message_data)

        channel.basic_consume(queue=queue_name, on_message_callback=check_message, auto_ack=True)

        def start_consuming():
            channel.start_consuming()

        thread = threading.Thread(target=start_consuming)
        thread.daemon = True  # Daemonize thread
        thread.start()

        return future

    def consume(self, queue, callback):
        connection = self._connect()
        channel = connection.channel()
        channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=False)

        def start_consuming():
            print(' [*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()

        thread = threading.Thread(target=start_consuming)
        thread.start()

# Usage in your FastAPI app
client = RabbitMQClient()
