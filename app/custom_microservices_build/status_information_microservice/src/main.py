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

# Save aggregated transaction data to PostgreSQL
def save_to_postgres(conn, transaction):
    if DBLESS_MODE:
        print("Aggregated Transaction Data (DBLESS_MODE):")
        print(json.dumps(transaction, indent=2))
    else:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO transactions_aggregated (transaction_id, store_id, timestamp, total_price)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (transaction_id) DO NOTHING;
                    """,
                    (
                        transaction["transaction_id"],
                        transaction["store_id"],
                        datetime.fromisoformat(transaction["timestamp"]),
                        transaction["total_price"]
                    )
                )
            conn.commit()
            print(f"Saved transaction {transaction['transaction_id']} to PostgreSQL.")
        except Exception as e:
            print(f"Error saving to PostgreSQL: {e}")
            conn.rollback()

# Check if the Kafka topic exists
def check_topic_exists():
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=[KAFKA_BROKER])
        topics = admin_client.list_topics()
        if TOPIC not in topics:
            print(f"Topic '{TOPIC}' does not exist. Please create the topic before consuming messages.")
            return False
        print(f"Topic '{TOPIC}' found. Proceeding with consumption.")
        return True
    except Exception as e:
        print(f"Error connecting to Kafka AdminClient or checking topic existence: {e}")
        return False
    finally:
        admin_client.close()

# Consume and process messages from Kafka
def consume_and_process():
    # Ensure topic exists
    if not check_topic_exists():
        print("Exiting as the topic does not exist.")
        return

    # Connect to PostgreSQL unless DBLESS_MODE is enabled
    conn = connect_to_postgres()
    if not DBLESS_MODE and conn is None:
        print("Failed to connect to PostgreSQL. Exiting.")
        return

    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=f'transaction_group'
    )

    print("Started consuming messages from Kafka...")

    try:
        while True:
            message_batch = consumer.poll(timeout_ms=5000)

            if message_batch:
                for tp, messages in message_batch.items():
                    for message in messages:
                        transaction_data = message.value

                        # Perform data validation
                        if not ("transaction_id" in transaction_data and "store_id" in transaction_data and "timestamp" in transaction_data and "total_price" in transaction_data):
                            print(f"Invalid message structure: {transaction_data}")
                            continue

                        # Save transaction data to PostgreSQL or output to stdout
                        save_to_postgres(conn, transaction_data)
                        print("Message processed and saved.")
            else:
                print("No messages found in this poll cycle. Checking again.")

            sleep(1)  # Small sleep to reduce CPU usage during polling
    except KeyboardInterrupt:
        print("Consumption interrupted.")
    finally:
        # Close connections if connected to PostgreSQL
        consumer.close()
        if conn:
            conn.close()
        print("Connections closed.")

if __name__ == "__main__":
    consume_and_process()
