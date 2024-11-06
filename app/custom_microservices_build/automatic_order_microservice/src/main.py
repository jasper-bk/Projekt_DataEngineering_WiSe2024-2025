#!/usr/bin/env python3

import os
import json
from kafka import KafkaConsumer, KafkaAdminClient
from datetime import datetime
from time import sleep
import random

# Kafka and PostgreSQL configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9094')
TOPIC = os.getenv('KAFKA_TOPIC', 'inbound_checkout')


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

                        # To-Do: Perform data validation

                        # To-o: Check inventory and make a api call to order new stuff if the treshold is not met

                        # To-Do: Make an api call
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
