# --- Redis Configuration ---
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Input key (raw data from the ingest service)
REDIS_INPUT_LIST = "wikipedia_events"

# Output key prefix for the processed data
# Creating two lists: live feed and vandalism alerts
REDIS_OUTPUT_KEY_PREFIX = "processed_edits"
LIVE_FEED_LIST = f"{REDIS_OUTPUT_KEY_PREFIX}:live_feed"
VANDALISM_FEED_LIST = f"{REDIS_OUTPUT_KEY_PREFIX}:vandalism_feed"

# --- Vandalism Detection Rules ---

# List of keywords to flag in edit comments. Case-insensitive.
VANDALISM_KEYWORDS = [
    "vandalism",
    "revert",
    "spam",
    "nonsense",
    "test edit",
    "undo",
    "blanking",
]

# Number of bytes removed by an anonymous user to be considered suspicious.
# Negative number indicates deletion
LARGE_DELETION_THRESHOLD = -300

# Number of bytes added by a brand new user to be considered suspicious.
LARGE_ADDITION_NEW_USER_THRESHOLD = 500
