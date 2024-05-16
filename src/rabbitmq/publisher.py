import json
import pika
from src.config.settings import settings, logger

conf = {
    'host': settings.rabbit_host,
    'port': '5672',
    'q_name': settings.rabbit_queue,
    'login': settings.username,
    'password': settings.passw,
}


class Publisher:
    def __init__(self, config: dict):
        self._config = config
        self._queue_name = self._config['q_name']
        self._connection = None
        self._channel = None

    def _init_all(self):
        if self._connection is None:
            self._connection = self.create_connection()
            self._channel = self._connection.channel()
            self._publish_q = self._channel.queue_declare(
                queue=self._queue_name,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': 'dlx_exchange',
                    'x-dead-letter-routing-key': 'dlx_key',
                    'x-queue-type': 'quorum',
                    'x-delivery-limit': 5,
                },
            )

    def publish_message(self, message: dict):
        self._init_all()
        logger.debug(f'publishing message: {message}')
        self._channel.basic_publish(
            exchange='',
            routing_key=self._queue_name,
            properties=pika.BasicProperties(),
            body=json.dumps(message),
        )

    def create_connection(self) -> pika.BlockingConnection:
        params = pika.ConnectionParameters(
            host=self._config['host'],
            port=self._config['port'],
            credentials=pika.PlainCredentials(
                username=self._config['login'], password=self._config['password']
            ),
        )
        return pika.BlockingConnection(params)


publisher = Publisher(conf)
