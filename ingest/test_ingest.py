import pytest
from unittest.mock import MagicMock, patch

# Import ingest module components
from .ingest import run_ingest
from . import config


# This is a sample SSE event message, converted to an object with a .data attribute
# to simulate the real sseclient event object.
class MockSSEEvent:
    def __init__(self, data, event="message"):
        self.data = data
        self.event = event


# Sample JSON string mimicking Wikimedia stream message
SAMPLE_EVENT_DATA = '{"title": "Test Page", "user": "TestUser"}'
# Another sample stream message to test list trimming
SAMPLE_EVENT_DATA_2 = '{"title": "Test Page", "user": "TestUser"}'


@pytest.fixture
def mock_redis_client(mocker):
    """
    Creates a mock Redis client.
    We can inspect this mock object later to see if our code called the right methods.
    """
    # Create a mock instance of the redis.Redis class
    mock_redis = MagicMock()
    # Use mocker.patch to place the real redis.Redis with our mock
    mocker.patch("redis.Redis", return_value=mock_redis)
    return mock_redis


def test_push_to_redis(mocker, mock_redis_client):
    """
    This test ensures that when the run_ingest() function receives SSE events,
    it correctly calls the redis client's methods (rpush, ltrim, expire)
    """
    # Set up the mocks for external services

    # Mock the `connect_to_stream` function to yielf our fake events
    # instead of connecting to the real Wikipedia stream.
    mock_stream = [MockSSEEvent(SAMPLE_EVENT_DATA), MockSSEEvent(SAMPLE_EVENT_DATA_2)]

    mocker.patch("ingest.ingest.connect_to_stream", return_value=mock_stream)

    # Run the run_ingest function from ingest.py

    # Runs the loop exactly twice, then raises StopIteration
    # since we only have two sample events
    run_ingest()

    # Check if the mock Redis client was used as expected

    # Check that rpush was called twice
    assert mock_redis_client.rpush.call_count == 2

    # Check the arguments of the first rpush call
    mock_redis_client.rpush.assert_any_call(config.REDIS_STREAM_NAME, SAMPLE_EVENT_DATA)
    # Check the arguments of the second rpush call
    mock_redis_client.rpush.assert_any_call(
        config.REDIS_STREAM_NAME, SAMPLE_EVENT_DATA_2
    )

    # Check that ltrim and expire were also called twice
    assert mock_redis_client.ltrim.call_count == 2
    mock_redis_client.ltrim.assert_called_with(
        config.REDIS_STREAM_NAME, -config.MAX_RAW_EVENTS_IN_QUEUE, -1
    )

    assert mock_redis_client.expire.call_count == 2
    mock_redis_client.expire.assert_called_with(
        config.REDIS_STREAM_NAME, config.QUEUE_KEY_TTL
    )

    print("\n Test passed: Redis client was called with the correct commands.")
