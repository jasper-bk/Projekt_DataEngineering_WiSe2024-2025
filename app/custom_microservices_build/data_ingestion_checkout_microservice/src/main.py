#!/usr/bin/env python3

import json
import os
import random
import datetime
import time
import uuid
from kafka import KafkaProducer, KafkaAdminClient
from kafka.errors import KafkaError
from kafka.admin import NewTopic

# Set default Kafka configuration, override with environment variables if available
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9094')
TOPIC = os.getenv('KAFKA_TOPIC', 'inbound_checkout')

# Sample data for stores and products
stores = [
    {"store_id": "001"},
    {"store_id": "002"},
    {"store_id": "003"},
]

products = [
    {"product_id": "P001", "price": 0.5},
    {"product_id": "P002", "price": 1.2},
    {"product_id": "P003", "price": 0.8},
    {"product_id": "P004", "price": 2.5},
    {"product_id": "P005", "price": 1.5},
]

# Function to check and create topic if it doesn't exist
def ensure_topic_exists(topic_name, broker):
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=[broker])
        topics = admin_client.list_topics()

        if topic_name not in topics:
            print(f"Topic '{topic_name}' does not exist. Creating topic...")
            topic = NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
            admin_client.create_topics([topic])
            print(f"Topic '{topic_name}' created successfully.")
        else:
            print(f"Topic '{topic_name}' already exists.")
        admin_client.close()
    except Exception as e:
        print(f"Error while ensuring topic exists: {e}")
        raise

# Function to generate fake transaction data
def generate_transaction(store):
    num_items = random.randint(1, 5)

    items = []
    total_price = 0.0

    for _ in range(num_items):
        product = random.choice(products)
        quantity = random.randint(1, 10)
        price = product["price"] * quantity
        total_price += price

        items.append({
            "product_id": product["product_id"],
            "quantity": quantity,
            "total_price": price
        })

    transaction = {
        "transaction_id": f"TXN_{random.randint(1000, 9999)}",
        "timestamp": datetime.datetime.now().isoformat(),
        "store_id": store["store_id"],
        "items": items,
        "total_price": round(total_price, 2)
    }

    return transaction

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

# Main function
def main():
    # Select a random store at startup
    store = random.choice(stores)
    print(f"Using store ID: {store['store_id']} for transactions")

    # Ensure connection to Kafka
    if not check_kafka_connection(KAFKA_BROKER):
        print("Exiting due to inability to connect to Kafka.")
        return

    # Ensure the topic exists
    ensure_topic_exists(TOPIC, KAFKA_BROKER)

    # Initialize Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        key_serializer=lambda k: str(k).encode('utf-8'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks=1,
        linger_ms=10,
        batch_size=16384,
        request_timeout_ms=60000,
        retries=3
    )

    # Loop to send fake data to Kafka
    try:
        while True:
            transaction_data = generate_transaction(store)
            key = str(uuid.uuid4())  # Generate a unique UUID key
            future = producer.send(TOPIC, key=key, value=transaction_data)
            try:
                record_metadata = future.get(timeout=10)
                print(f"Message with key {key} sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            except Exception as e:
                print(f"Error sending message: {e}")
            print(f"Sent: {transaction_data}")
            time.sleep(random.uniform(0.5, 2.0))  # Random delay between transactions
    except KeyboardInterrupt:
        print("Data stream stopped.")
    finally:
        producer.close()

# Run main function if this file is executed as a script
if __name__ == '__main__':
    main()
