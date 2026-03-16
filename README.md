
---

# Energy Monitoring IoT Pipeline

A hands-on project demonstrating a **generic IoT energy monitoring pipeline** using managed services and Python-based device simulation.

The project simulates a fleet of devices sending electrical telemetry to a cloud message broker, which is then ingested into a time-series database and visualized using Grafana dashboard.

---

# Architecture Overview

The system architecture:

```
IoT Energy Meter (Simulated)
        │
        ▼
CloudAMQP (LavinMQ) Queue
        │
        ▼
Python Ingestion Service
        │
        ▼
InfluxDB 3 (Time-Series Database)
        │
        ▼
Grafana Dashboards
```

Pipeline flow:

```
Producer(s) → CloudAMQP Queue → Consumer → InfluxDB → Grafana
```

Each component has a clearly defined role:

| Component        | Role                                              |
| ---------------- | ------------------------------------------------- |
| Python Producers | Simulated energy meters sending telemetry         |
| CloudAMQP        | Managed message broker buffering device data      |
| Python Consumer  | Reads queue messages and stores them               |
| InfluxDB 3       | Time-series database for electrical telemetry     |
| Grafana          | Visualization dashboards                          |

---

# Project Structure

```
iot-energy-monitoring/
│
├── requirements.txt
├── .env.example
├── README.md
│
├── scripts/
│   ├── test_broker_connection.py
│   └── test_influx_write.py
│
├── producers/
│   ├── single_device_producer.py
│   └── fleet_device_simulator.py
│
├── consumers/
│   ├── queue_message_logger.py
│   ├── minimal_amqp_to_influx.py
│   └── amqp_to_influx3.py
│
└── wokwi/
    ├── sketch.ino
    └── diagram.json
```

---

# Cloud Services Setup

## CloudAMQP

- Signup on cloudamqp.com using free tier
- Click Create New Instance using LavinMQ
- Pick a name for the instance, select the free plan and choose a region
- Go to instance dashboard and copy the AMQP URL. Put it on .env

## InfluxDB

- Signup on cloud2.influxdata.com using free tier
- On Resource Center, click Manage Database & Security and choose Go To Buckets to create a database and choose Go To Tokens to generate API Token
- Put following lines on .env:
```
INFLUX3_HOST=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUX3_ORG=[org name on top left]
INFLUX3_DATABASE=[name of database]
INFLUX3_TOKEN=[api token generated]
```

## Grafana

- Signup on grafana.com using free tier
- Go to Connections → Add new connection
- Add InfluxDB
- Configure setting with following information:
```
URL: Use previously set INFLUX3_HOST
Product: InfluxDB Cloud Serverless
Query Language: SQL
Database: energy-monitoring
Token: use previously set INFLUX3_TOKEN
```
- Click Save & Test to verify
- If successful, create a new Dashboard → Add visualization → select your InfluxDB data source

# Environment Setup

## 1 Install Python

Recommended:

```
Python 3.10+
```

Check version:

```bash
python --version
```

---

## 2 Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## 3 Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies:

| Package          | Purpose                          |
| ---------------- | -------------------------------- |
| pika             | AMQP client for CloudAMQP        |
| influxdb3-python | InfluxDB client                  |
| python-dotenv    | Load environment variables       |
| pandas           | Used for query output formatting |

---

# Environment Configuration

Create a `.env` file from the template.

```bash
cp .env.example .env
```

Edit `.env`:

```
CLOUDAMQP_URL=amqps://USERNAME:PASSWORD@dog.lmq.cloudamqp.com/VHOST

INFLUX3_HOST=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUX3_ORG=Dev
INFLUX3_DATABASE=energy-monitoring
INFLUX3_TOKEN=YOUR_INFLUX_TOKEN
```

Required values:

| Variable         | Description                     |
| ---------------- | ------------------------------- |
| CLOUDAMQP_URL    | CloudAMQP broker connection URL |
| INFLUX3_HOST     | InfluxDB Cloud endpoint         |
| INFLUX3_ORG      | Influx organization             |
| INFLUX3_DATABASE | Database name                   |
| INFLUX3_TOKEN    | API token                       |

---

# Script Overview

## scripts/

### test_broker_connection.py

Purpose:

Test connectivity to CloudAMQP.

Steps performed:

1. connect to AMQP broker
2. declare queue
3. publish test message
4. close connection

Run:

```bash
python scripts/test_broker_connection.py
```

Expected output:

```
[OK] Queue declared
[OK] Test message published
```

---

### test_influx_write.py

Purpose:

Validate InfluxDB connectivity.

Functions:

* write sample points
* execute SQL query
* print query results

Run:

```bash
python scripts/test_influx_write.py
```

Expected output:

```
STEP 1: Writing test points
STEP 2: Running query
STEP 3: Query results
```

---

# Producer Scripts

Producer scripts simulate energy meters sending electrical telemetry.

Queue used:

```
energy_telemetry
```

---

## single_device_producer.py

Simulates one energy meter with static values.

Telemetry example:

```json
{
  "device_id": "meter-001",
  "voltage": 230.5,
  "current": 4.2,
  "power": 967.3,
  "energy": 15.6,
  "power_factor": 0.94,
  "frequency": 50.0
}
```

Run:

```bash
python producers/single_device_producer.py
```

---

## fleet_device_simulator.py

Simulates multiple energy meters concurrently.

Features:

* multiple device threads
* randomized electrical telemetry
* random publish intervals

Run:

```bash
python producers/fleet_device_simulator.py
```

Default simulation:

```
20 meters
```

Example output:

```
[PUB] meter-005 -> {...}
[PUB] meter-012 -> {...}
```

---

# Consumer Scripts

Consumers read queue messages and process them.

---

## queue_message_logger.py

Simple debugging consumer.

Purpose:

Inspect raw messages in the queue.

Run:

```bash
python consumers/queue_message_logger.py
```

Output example:

```
[MSG] {"device_id":"meter-001",...}
```

---

## minimal_amqp_to_influx.py

Minimal ingestion pipeline.

Workflow:

```
AMQP Queue → InfluxDB
```

Stores limited fields:

* device_id
* voltage
* power

Run:

```bash
python consumers/minimal_amqp_to_influx.py
```

---

## amqp_to_influx3.py

Full ingestion service used listen for data producer.

Workflow:

```
Queue message
    ↓
JSON decode
    ↓
InfluxDB Point
    ↓
Write to database
```

Stored fields:

| Tag         | Field         |
| ----------- | ------------- |
| device_id   | voltage       |
|             | current       |
|             | power         |
|             | energy        |
|             | power_factor  |
|             | frequency     |

Run:

```bash
python consumers/amqp_to_influx3.py
```

Output:

```
[WRITE] meter-004 -> InfluxDB 3
```

---

# Running the End-to-End Demo

Open two terminals.

---

## Terminal 1

Start ingestion service -> Consumer

```bash
python consumers/amqp_to_influx3.py
```

---

## Terminal 2

Start fleet simulator -> Producer

```bash
python producers/fleet_device_simulator.py
```

---

## Expected behavior

Producer output:

```
[PUB] meter-003 -> {...}
```

Consumer output:

```
[WRITE] meter-003 -> InfluxDB 3
```

CloudAMQP:

```
Queue activity visible
```

InfluxDB:

```
Rows increasing
```

---

# Querying Data in InfluxDB

Example SQL queries.

---

## Latest telemetry

```sql
SELECT *
FROM energy_telemetry
ORDER BY time DESC
LIMIT 20;
```

---

## Average power consumption

```sql
SELECT
AVG(power)
FROM energy_telemetry;
```

---

## Energy consumption by device

```sql
SELECT
device_id,
SUM(energy)
FROM energy_telemetry
GROUP BY device_id;
```

---

# Grafana Dashboards

Recommended panels.

---

## Power consumption over time

```
time series chart
```

Query:

```sql
SELECT time, power
FROM energy_telemetry
```

---

## Voltage stability

```
time series chart
```

Query:

```sql
SELECT time, voltage
FROM energy_telemetry
```

---

## Energy usage by device

```
bar gauge
```

Query:

```sql
SELECT device_id, SUM(energy)
FROM energy_telemetry
GROUP BY device_id
```

---

# Troubleshooting

## Broker connection fails

Check:

* CLOUDAMQP_URL
* network connectivity
* TLS port

Test with:

```bash
python scripts/test_broker_connection.py
```

---

## Influx authentication error

Error example:

```
401 unauthorized
```

Solution:

* regenerate API token
* confirm org name
* verify database name

Test with:

```bash
python scripts/test_influx_write.py
```

---

## Queue receives no messages

Check:

* producer running
* queue name matches
* broker dashboard

---

# Summary

This project demonstrates a scalable IoT energy monitoring pipeline using:

* Python energy meter simulation
* managed AMQP messaging
* time-series storage
* real-time dashboards

Key concept demonstrated:

```
Decoupled cloud ingestion using message queues
```

---
