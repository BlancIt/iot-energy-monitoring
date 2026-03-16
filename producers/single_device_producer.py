import json
import os
import time
from datetime import datetime, timezone

import pika
from dotenv import load_dotenv

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "energy_telemetry"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_payload() -> dict:
    return {
        "device_id": "meter-001",
        "voltage": 230.5,
        "current": 4.2,
        "power": 967.3,
        "energy": 15.6,
        "power_factor": 0.94,
        "frequency": 50.0,
        "ts": now_iso(),
    }


def main() -> None:
    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")

    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    print("[OK] Single device producer connected")

    try:
        while True:
            payload = make_payload()
            body = json.dumps(payload)
            channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=body)
            print("[PUB]", body)
            time.sleep(5)
    finally:
        connection.close()
        print("[OK] Connection closed")


if __name__ == "__main__":
    main()