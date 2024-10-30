#!/usr/bin/env python3

import json
import os
import random
import datetime
import time
from kafka import KafkaProducer, KafkaAdminClient

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

# Function to check if the topic exists
def topic_exists(topic_name, broker):
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=[broker])
        topics = admin_client.list_topics()
        admin_client.close()
        return topic_name in topics
    except Exception as e:
        print(f"Error retrieving topic list: {e}")
        return False

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

    # Optional: Include customer-related information here if desired.
    # For example, payment method, payment provider, loyalty card usage, etc.

    return transaction

# Main function
def main():
    # Select a random store at startup
    store = random.choice(stores)
    print(f"Using store ID: {store['store_id']} for transactions")

    # Check if the topic exists
    if not topic_exists(TOPIC, KAFKA_BROKER):
        print(f"Topic '{TOPIC}' does not exist. Please create the topic before sending messages.")
        return

    # Initialize Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
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
            future = producer.send(TOPIC, value=transaction_data)
            try:
                record_metadata = future.get(timeout=10)
                print(f"Message sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
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
