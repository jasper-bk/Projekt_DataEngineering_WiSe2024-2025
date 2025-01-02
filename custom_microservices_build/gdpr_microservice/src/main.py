#!/usr/bin/env python3

import os
import json
import psycopg2
from kafka import KafkaConsumer, KafkaAdminClient
from datetime import datetime
from time import sleep
import random

# Kafka and PostgreSQL configuration. Loaded from environment variables. Will be defaulted, if null
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9094')
TOPIC = os.getenv('KAFKA_TOPIC', 'inbound_checkout')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'application-user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'no-secret-default-password')
DBLESS_MODE = os.getenv('DBLESS_MODE', 'true').lower() == 'false'

# Connect to PostgreSQL (if not in DBLESS_MODE)
def connect_to_postgres():
    if DBLESS_MODE:
        print("DBLESS_MODE is active. Skipping database connection.")
        return None
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# Consume and process messages from Kafka
def main():

    # Connect to PostgreSQL unless DBLESS_MODE is enabled
    conn = connect_to_postgres()
    if not DBLESS_MODE and conn is None:
        print("Failed to connect to PostgreSQL. Exiting.")
        return

    # No business logic is built into the project as this is not sufficiently defined
    # To-Do if business logic is sufficiently defined : Run delete statements in direction of PostgreSQL to delete data which is no longer allowed to have

if __name__ == "__main__":
    main()
