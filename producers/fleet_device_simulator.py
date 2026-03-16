import json
import os
import random
import signal
import threading
import time
from datetime import datetime, timezone

import pika
from dotenv import load_dotenv

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "energy_telemetry"

RUNNING = True


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_payload(device_id: str) -> dict:
    voltage = round(random.uniform(210, 240), 2)
    current = round(random.uniform(0.5, 15.0), 2)
    power_factor = round(random.uniform(0.70, 1.00), 2)
    power = round(voltage * current * power_factor, 2)
    return {
        "device_id": device_id,
        "voltage": voltage,
        "current": current,
        "power": power,
        "energy": round(random.uniform(0.1, 50.0), 2),
        "power_factor": power_factor,
        "frequency": round(random.uniform(49.8, 50.2), 2),
        "ts": now_iso(),
    }


def device_loop(device_id: str, interval_range=(2, 6)) -> None:
    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    try:
        while RUNNING:
            payload = make_payload(device_id)
            body = json.dumps(payload)
            channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=body)
            print(f"[PUB] {device_id} -> {body}")
            time.sleep(random.uniform(*interval_range))
    finally:
        connection.close()


def stop_handler(signum, frame) -> None:
    del signum, frame
    global RUNNING
    RUNNING = False


def main(num_devices: int = 20) -> None:
    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    threads = []
    for i in range(1, num_devices + 1):
        device_id = f"meter-{i:03d}"

        thread = threading.Thread(
            target=device_loop,
            args=(device_id,),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    while RUNNING:
        time.sleep(1)

    for thread in threads:
        thread.join(timeout=1)


if __name__ == "__main__":
    main()