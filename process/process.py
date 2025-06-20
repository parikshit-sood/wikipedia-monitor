import json
import redis
import time

# Import configation from config.py file within the same package
from . import config


def check_for_vandalism(edit_data):
    """
    Applies a set of heuristic rules to flag potential vandalism.
    Return a list of reasons if vandalism is suspected, else an empty list.
    """
    flags = []
    edit_size_bytes = edit_data.get("length", {}).get("new", 0) - edit_data.get(
        "length", {}
    ).get("old", 0)

    # Rule 1: Large deletion by anonymous user
    if (
        edit_data.get("user_is_anonymous")
        and edit_size_bytes < config.LARGE_DELETION_THRESHOLD
    ):
        flags.append(f"Large deletion ({edit_size_bytes} bytes) by an anonymous user.")

    # Rule 2: Use of blacklisted keywords in the summary (case-insensitive)
    comment = edit_data.get("comment", "").lower()
    for keyword in config.VANDALISM_KEYWORDS:
        if keyword in comment:
            flags.append(f"Suspicious keyword in summary: '{keyword}'.")
            break

    # Rule 3: Very large addition by a brand new user
    user_edit_count = edit_data.get("performer", {}).get("user_edit_count", 0)
    if (
        user_edit_count == 1
        and edit_size_bytes > config.LARGE_ADDITION_NEW_USER_THRESHOLD
    ):
        flags.append(f"Unusually large first edit ({edit_size_bytes} bytes).")

    return flags


def run_process():
    """
    Run the processing engine.
    """
    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True,  # Decode from bytes to strings automatically
    )
    print("Processing engine started. Waiting for events...")

    while True:
        try:
            # Use BLPOP blocking command. It returns a tuple: (list_name, item_data). Timeout=0 means wait forever.
            _, raw_data = redis_client.blpop(config.REDIS_INPUT_LIST, timeout=0)

            data = json.loads(raw_data)

            # Enrich the data with vandalism check
            vandalism_flags = check_for_vandalism(data)
            data["is_vandalism"] = bool(vandalism_flags)
            data["vandalism_reasons"] = vandalism_flags

            # Push processed data to appropriate lists
            processed_data_str = json.dumps(data)

            # Add to general "live feed" list and cap its size at 100
            redis_client.lpush(config.LIVE_FEED_LIST, processed_data_str)
            redis_client.ltrim(config.LIVE_FEED_LIST, 0, 99)

            # If it's flagged, also add it to the vandalism feed and cap at 50
            if data["is_vandalism"]:
                print(
                    f"\nVandalism detected: {data.get('title')} - Reasons: {', '.join(vandalism_flags)}"
                )
                redis_client.lpush(config.VANDALISM_FEED_LIST, processed_data_str)
                redis_client.ltrim(config.VANDALISM_FEED_LIST, 0, 49)

        except json.JSONDecodeError:
            print(f"\nSkipping malformed JSON data: {raw_data[:100]}...")
            continue

        except Exception as e:
            print(f"\nUnexpected error ocurred: {e}")
            time.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    run_process()
