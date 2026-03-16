import json
import os
import sys

import pika
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "energy_telemetry"

TOKEN = os.getenv("INFLUX3_TOKEN")
ORG = os.getenv("INFLUX3_ORG")
HOST = os.getenv("INFLUX3_HOST")
DATABASE = os.getenv("INFLUX3_DATABASE")


def callback(ch, method, properties, body):
    del ch, method, properties
    
    try:
        data = json.loads(body.decode("utf-8"))
        point = (
            Point("energy_telemetry")
            .tag("device_id", data["device_id"])
            .field("voltage", float(data["voltage"]))
            .field("power", float(data["power"]))
        )
        client.write(database=DATABASE, record=point)
        print("[WRITE]", data["device_id"])
    except Exception as exc:
        print("[ERROR]", exc)

def main() -> None:
    global client

    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")
    if not all([TOKEN, ORG, HOST, DATABASE]):
        raise RuntimeError("Missing one or more InfluxDB 3 env vars in .env")

    client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    print("[OK] Minimal AMQP -> Influx bridge connected")
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
    client = None
    main()