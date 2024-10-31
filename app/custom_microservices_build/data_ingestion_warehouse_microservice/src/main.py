#!/usr/bin/env python3

import json
import os
import random
import datetime
import time
from kafka import KafkaProducer, KafkaAdminClient

# Set default Kafka configuration, override with environment variables if available
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9094')
TOPIC = os.getenv('KAFKA_TOPIC', 'warehouse_inventory')

# Sample data for warehouses and items
warehouses = [
    {"warehouse_id": "WH01", "location": "Berlin"},
    {"warehouse_id": "WH02", "location": "Hamburg"},
    {"warehouse_id": "WH03", "location": "Munich"},
]

items = [
    {"item_id": "IT001", "item_name": "Widget A", "unit_price": 5.0},
    {"item_id": "IT002", "item_name": "Widget B", "unit_price": 12.5},
    {"item_id": "IT003", "item_name": "Widget C", "unit_price": 8.0},
    {"item_id": "IT004", "item_name": "Widget D", "unit_price": 25.0},
    {"item_id": "IT005", "item_name": "Widget E", "unit_price": 15.5},
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

# Function to generate fake inventory movement data
def generate_inventory_movement(warehouse):
    num_items = random.randint(1, 5)

    movements = []
    total_value = 0.0

    for _ in range(num_items):
        item = random.choice(items)
        quantity = random.randint(1, 100)
        movement_type = random.choice(["inbound", "outbound"])
        value = item["unit_price"] * quantity
        total_value += value

        movements.append({
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "quantity": quantity,
            "movement_type": movement_type,
            "total_value": round(value, 2)
        })

    inventory_movement = {
        "movement_id": f"MOV_{random.randint(1000, 9999)}",
        "timestamp": datetime.datetime.now().isoformat(),
        "warehouse_id": warehouse["warehouse_id"],
        "location": warehouse["location"],
        "movements": movements,
        "total_value": round(total_value, 2)
    }

    return inventory_movement

# Main function
def main():
    # Select a random warehouse at startup
    warehouse = random.choice(warehouses)
    print(f"Using warehouse ID: {warehouse['warehouse_id']} in {warehouse['location']} for inventory movements")

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
            inventory_data = generate_inventory_movement(warehouse)
            future = producer.send(TOPIC, value=inventory_data)
            try:
                record_metadata = future.get(timeout=10)
                print(f"Message sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            except Exception as e:
                print(f"Error sending message: {e}")
            print(f"Sent: {inventory_data}")
            time.sleep(random.uniform(0.5, 2.0))  # Random delay between movements
    except KeyboardInterrupt:
        print("Data stream stopped.")
    finally:
        producer.close()

# Run main function if this file is executed as a script
if __name__ == '__main__':
    main()
