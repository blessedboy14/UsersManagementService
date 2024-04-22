import json
import pika
from src.config.settings import settings


conf = {
    'host': settings.rabbit_host,
    'port': '5672',
    'q_name': 'reset-password-stream',
    'login': settings.username,
    'password': settings.passw,
}


class Publisher:
    def __init__(self, config: dict):
        self._config = config
        self._queue_name = self._config['q_name']
        self._connection = self.create_connection()
        self._channel = self._connection.channel()
        self._publish_q = self._channel.queue_declare(queue=self._queue_name)

    def publish_message(self, message: dict):
        self._channel.basic_publish(
            exchange='',
            routing_key=self._queue_name,
            properties=pika.BasicProperties(),
            body=json.dumps(message),
        )

    def create_connection(self):
        params = pika.ConnectionParameters(
            host=self._config['host'],
            port=self._config['port'],
            credentials=pika.PlainCredentials(
                username=self._config['login'], password=self._config['password']
            ),
        )
        return pika.BlockingConnection(params)


publisher = Publisher(conf)
