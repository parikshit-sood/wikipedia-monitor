# --- Stream Configuration ---
WIKIMEDIA_STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"

# --- Redis Configuration ---
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_STREAM_NAME = "wikipedia_events"

# --- Sizing & TTL Configuration ---
MAX_RAW_EVENTS_IN_QUEUE = (
    10000  # Max number of raw (pre-processed) events to keep in buffer
)
QUEUE_KEY_TTL = 3600  # Key is marked as volatile and discarded after 1 hour
