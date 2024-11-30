#!/usr/bin/env python3

import os
import json
from kafka import KafkaConsumer, KafkaAdminClient
from datetime import datetime
from time import sleep
import random
import time
from kafka.errors import KafkaError

# Kafka configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9094')
TOPIC = os.getenv('KAFKA_TOPIC', 'inbound_checkout')

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

# Placeholder for data validation (this would be where real validation logic goes)
def validate_transaction_data(transaction_data):
    # Simulate data validation
    print(f"Validating transaction data for transaction ID: {transaction_data['transaction_id']}")
    # Placeholder logic (assuming data is always valid)
    return True

# Placeholder for inventory check and API call if threshold is not met
def check_inventory_and_order(transaction_data):
    print(f"Checking inventory for transaction {transaction_data['transaction_id']}...")
    # Placeholder: Simulate inventory check
    inventory_level = random.randint(0, 10)  # Random inventory level for simulation

    # Check if the inventory is below a threshold (e.g., less than 5 items in stock)
    if inventory_level < 5:
        print(f"Inventory below threshold for product {transaction_data['items'][0]['product_id']}. Placing order.")
        order_new_inventory(transaction_data)
    else:
        print(f"Inventory sufficient for product {transaction_data['items'][0]['product_id']}. No order needed.")

# Placeholder for API call to order new inventory
def order_new_inventory(transaction_data):
    print(f"Ordering new inventory for product {transaction_data['items'][0]['product_id']}...")
    # Placeholder for API logic (e.g., sending a request to an external service)
    # Simulate successful ordering
    print(f"Order placed successfully for product {transaction_data['items'][0]['product_id']}.")

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

                        # Data validation
                        if validate_transaction_data(transaction_data):
                            print(f"Transaction data valid: {transaction_data['transaction_id']}")

                            # Inventory check and order placement if threshold is not met
                            check_inventory_and_order(transaction_data)
                        else:
                            print(f"Invalid transaction data: {transaction_data['transaction_id']}")

            else:
                print("No messages found in this poll cycle. Checking again.")

            sleep(1)  # Small sleep to reduce CPU usage during polling

    except KeyboardInterrupt:
        print("Consumption interrupted.")
    finally:
        consumer.close()
        print("Connections closed.")

if __name__ == "__main__":
    # Ensure connection to Kafka
    if not check_kafka_connection(KAFKA_BROKER):
        print("Exiting due to inability to connect to Kafka.")
    else:
        consume_and_process()
