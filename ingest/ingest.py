import sseclient
import requests
import json
import redis
import time

# Import configuration from config.py
from . import config


def connect_to_stream():
    """
    Connects to the Wikimedia SSE stream with retry logic.
    Yields events as they are received
    """

    while True:
        try:
            print("Connecting to Wikimedia stream...")
            client = sseclient.SSEClient(
                requests.get(config.WIKIMEDIA_STREAM_URL, stream=True)
            )
            print("Connection successful. Listening for events...")

            for event in client.events():
                yield event
        except (requests.exceptions.ConnectionError, json.JSONDecodeError) as e:
            print(f"Connection lost: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(
                f"An unexpected error has occurred: {e}. Reconnecting in 10 seconds..."
            )
            time.sleep(10)


def run_ingest():
    """
    Run ingestion service
    """
    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    print("Connected to Redis.")

    for event in connect_to_stream():
        if event.event == "message":
            # Push the event to the right of the list
            redis_client.rpush(config.REDIS_STREAM_NAME, event.data)

            # Proactively trim event list to maintain a max size (memory upperbound for Redis)
            redis_client.ltrim(
                config.REDIS_STREAM_NAME, -config.MAX_RAW_EVENTS_IN_QUEUE, -1
            )

            # Set TTL to mark it as volatile per the eviction policy
            redis_client.expire(config.REDIS_STREAM_NAME, config.QUEUE_KEY_TTL)

            print(".", end="", flush=True)


if __name__ == "__main__":
    run_ingest()
