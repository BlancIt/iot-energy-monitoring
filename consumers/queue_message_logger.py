import os
import sys

import pika
from dotenv import load_dotenv

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "energy_telemetry"


def callback(ch, method, properties, body):
    del ch, method, properties
    print("[MSG]", body.decode("utf-8"))


def main() -> None:
    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")

    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    print("[OK] Queue logger connected")
    print("[WAIT] Waiting for messages. Press CTRL+C to exit.")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[STOP] Interrupted by user")
        try:
            connection.close()
        finally:
            sys.exit(0)


if __name__ == "__main__":
    main()