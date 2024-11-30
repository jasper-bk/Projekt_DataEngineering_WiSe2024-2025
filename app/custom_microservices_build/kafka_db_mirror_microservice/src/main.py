#!/usr/bin/env python3

import os
import json
import psycopg2
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.errors import KafkaError
from datetime import datetime
import time

# Kafka and PostgreSQL configuration. Loaded from environment variables. Will be defaulted, if null
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9094')
TOPICS = os.getenv('KAFKA_TOPICS', 'inbound_checkout,warehouse_inventory').split(',')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'kafka_db_mirror')


POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'application-user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'no-secret-default-password')
DBLESS_MODE = os.getenv('DBLESS_MODE', 'true').lower() == 'false'

# Function to check Kafka connection
def check_kafka_connection(broker, timeout=60, interval=5):
    start_time = time.time()
    while True:
        try:
            # Try connecting to the Kafka broker
            admin_client = KafkaAdminClient(bootstrap_servers=[broker])
            admin_client.list_topics()
            admin_client.close()
            print(f"Connected to Kafka at {broker}")
            return True
        except KafkaError as e:
            # If Kafka is not reachable, wait and retry
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print(f"Could not connect to Kafka at {broker} within {timeout} seconds.")
                return False
            print(f"Kafka not reachable, retrying in {interval} seconds...")
            time.sleep(interval)

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

# Ensure a table exists in PostgreSQL for a given topic
def ensure_table_exists(conn, topic):
    if DBLESS_MODE:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {topic} (
                    id SERIAL PRIMARY KEY,
                    message JSONB,
                    received_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
            print(f"Table '{topic}' ensured in PostgreSQL.")
    except Exception as e:
        print(f"Error ensuring table '{topic}': {e}")
        conn.rollback()

# Save message to PostgreSQL
def save_to_postgres(conn, topic, message):
    if DBLESS_MODE:
        print(f"Message for topic '{topic}' (DBLESS_MODE):")
        print(json.dumps(message, indent=2))
    else:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {topic} (message)
                    VALUES (%s);
                    """,
                    (json.dumps(message),)
                )
            conn.commit()
            print(f"Saved message to table '{topic}'.")
        except Exception as e:
            print(f"Error saving message to table '{topic}': {e}")
            conn.rollback()

# Check if the Kafka topics exist
def check_topics_exist():
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=[KAFKA_BROKER])
        topics = admin_client.list_topics()
        for topic in TOPICS:
            if topic not in topics:
                print(f"Topic '{topic}' does not exist. Please create the topic before consuming messages.")
                return False
        print(f"All topics found. Proceeding with consumption.")
        return True
    except Exception as e:
        print(f"Error connecting to Kafka AdminClient or checking topics: {e}")
        return False
    finally:
        admin_client.close()

# Consume and process messages from Kafka
def consume_and_process():
    # Ensure topics exist
    if not check_topics_exist():
        print("Exiting as one or more topics do not exist.")
        return

    # Connect to PostgreSQL unless DBLESS_MODE is enabled
    conn = connect_to_postgres()
    if not DBLESS_MODE and conn is None:
        print("Failed to connect to PostgreSQL. Exiting.")
        return

    # Ensure all tables exist
    if conn:
        for topic in TOPICS:
            ensure_table_exists(conn, topic)

    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=CONSUMER_GROUP
    )

    print("Started consuming messages from Kafka...")

    try:
        while True:
            message_batch = consumer.poll(timeout_ms=5000)

            if message_batch:
                for tp, messages in message_batch.items():
                    topic = tp.topic
                    for message in messages:
                        data = message.value

                        # Save message to PostgreSQL or output to stdout
                        save_to_postgres(conn, topic, data)
                        print(f"Message processed and saved for topic '{topic}'.")
            else:
                print("No messages found in this poll cycle. Checking again.")

            time.sleep(1)  # Small sleep to reduce CPU usage during polling
    except KeyboardInterrupt:
        print("Consumption interrupted.")
    finally:
        # Close connections if connected to PostgreSQL
        consumer.close()
        if conn:
            conn.close()
        print("Connections closed.")

if __name__ == "__main__":
    # Ensure connection to Kafka
    if not check_kafka_connection(KAFKA_BROKER):
        print("Exiting due to inability to connect to Kafka.")
    else:
        consume_and_process()
