#!/usr/bin/env python3

import os
import json
import uuid
from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
from kafka.errors import KafkaError
from datetime import datetime
import time

# Kafka configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9094')
TOPIC = os.getenv('KAFKA_TOPIC', 'inbound_checkout')
AGGREGATED_TOPIC = os.getenv('KAFKA_AGGREGATED_TOPIC', 'aggregated_checkout')

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

# Function to ensure that a topic exists
def ensure_topic_exists(topic_name):
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=[KAFKA_BROKER])
        topics = admin_client.list_topics()

        if topic_name not in topics:
            print(f"Topic '{topic_name}' does not exist. Creating topic...")
            from kafka.admin import NewTopic
            topic = NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
            admin_client.create_topics([topic])
            print(f"Topic '{topic_name}' created successfully.")
        else:
            print(f"Topic '{topic_name}' already exists.")
        admin_client.close()
    except Exception as e:
        print(f"Error while ensuring topic exists: {e}")
        raise

# Consume and process messages from Kafka
def consume_and_process():
    # Ensure both topics exist
    ensure_topic_exists(TOPIC)
    ensure_topic_exists(AGGREGATED_TOPIC)

    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=f'checkout_group'
    )

    # Initialize Kafka producer for aggregated results
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

    print("Started consuming messages from Kafka...")

    # Aggregation variables
    total_transactions = 0
    total_price = 0.0

    try:
        while True:
            message_batch = consumer.poll(timeout_ms=5000)

            if message_batch:
                for tp, messages in message_batch.items():
                    for message in messages:
                        transaction_data = message.value

                        # Aggregation logic
                        total_transactions += 1
                        total_price += transaction_data.get("total_price", 0)

                        # Print for logging
                        print(f"Processed transaction {transaction_data['transaction_id']}")

                        # Optionally: Perform additional data validation or transformations here

                # Periodic aggregation (e.g., every 10 transactions or after a time interval)
                aggregated_data = {
                    "timestamp": datetime.now().isoformat(),
                    "total_transactions": total_transactions,
                    "total_price": round(total_price, 2)
                }

                # Send aggregated data to new topic
                key = str(uuid.uuid4())  # Generate a unique UUID key
                producer.send(AGGREGATED_TOPIC, key=key, value=aggregated_data)
                print(f"Sent aggregated data: {aggregated_data}")

            else:
                print("No messages found in this poll cycle. Checking again.")

            time.sleep(1)  # Small sleep to reduce CPU usage during polling

    except KeyboardInterrupt:
        print("Consumption interrupted.")
    finally:
        # Close connections
        consumer.close()
        producer.close()
        print("Connections closed.")

if __name__ == "__main__":
    # Ensure connection to Kafka
    if not check_kafka_connection(KAFKA_BROKER):
        print("Exiting due to inability to connect to Kafka.")
    else:
        consume_and_process()
