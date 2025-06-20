import pytest
import json
from unittest.mock import MagicMock

# Import main driver function
from .process import run_process
from . import config

DEBUG = 1


@pytest.fixture
def mock_redis_client(mocker):
    """
    Creates a mock Redis client.
    """
    mock_redis = MagicMock()
    mocker.patch("redis.Redis", return_value=mock_redis)
    return mock_redis


def create_mock_edit_event(
    is_anonymous=False, old_length=1000, new_length=1000, comment="", user_edit_count=10
):
    """
    Creates sample Wikipedia edit data.
    """
    return json.dumps(
        {
            "title": "Test Page",
            "user_is_anonymous": is_anonymous,
            "length": {"old": old_length, "new": new_length},
            "comment": comment,
            "performer": {"user_edit_count": user_edit_count},
        }
    )


# --- Test Cases ---


def test_large_anonymous_deletion_is_flagged(mocker, mock_redis_client):
    """
    Tests if an anonymous user deleting a large amount of content is flagged.
    """
    if DEBUG == 1:
        print("Testing large anonymous deletion...")
    # Create an event representing a large deletion by an anonymous user
    event_data = create_mock_edit_event(
        is_anonymous=True,
        old_length=2000,
        new_length=1000,  # -1000 bytes, which is below the threshold
    )

    if DEBUG == 1:
        print("Mock event created.")
    # Make the mock Redis client return this event from blpop
    mock_redis_client.blpop.return_value = (config.REDIS_INPUT_LIST, event_data)

    if DEBUG == 1:
        print("Mock Redis client returning this event from blpop...")
    # Stop the loop after one run
    mock_redis_client.blpop.side_effect = [
        (config.REDIS_INPUT_LIST, event_data),
        KeyboardInterrupt,
    ]

    # Act: Run the main function, which will now exit after one loop
    with pytest.raises(KeyboardInterrupt):
        run_process()

    if DEBUG == 1:
        print("Stopped mock Redis client after one iteration")

    # Assert: Check that the event was pushed to the VANDALISM list
    mock_redis_client.lpush.assert_any_call(config.VANDALISM_FEED_LIST, mocker.ANY)
    # Get the data that was pushed
    pushed_data_str = mock_redis_client.lpush.call_args.args[1]
    pushed_data = json.loads(pushed_data_str)

    assert pushed_data["is_vandalism"] is True
    assert "Large deletion" in pushed_data["vandalism_reasons"][0]


def test_suspicious_keyword_is_flagged(mocker, mock_redis_client):
    """
    Tests if an edit with a suspicious keyword in the summary is flagged.
    """
    # Arrange: Create an event with a keyword from our config list
    event_data = create_mock_edit_event(comment="reverting nonsense edit")
    mock_redis_client.blpop.side_effect = [
        (config.REDIS_INPUT_LIST, event_data),
        KeyboardInterrupt,
    ]

    # Act
    with pytest.raises(KeyboardInterrupt):
        run_process()

    # Assert
    mock_redis_client.lpush.assert_any_call(config.VANDALISM_FEED_LIST, mocker.ANY)
    pushed_data_str = mock_redis_client.lpush.call_args.args[1]
    pushed_data = json.loads(pushed_data_str)

    assert pushed_data["is_vandalism"] is True
    assert "Suspicious keyword" in pushed_data["vandalism_reasons"][0]


def test_large_new_user_edit_is_flagged(mocker, mock_redis_client):
    """
    Tests if a very large first edit from a new user is flagged.
    """
    # Arrange
    event_data = create_mock_edit_event(
        user_edit_count=1,  # This is the user's first edit
        old_length=100,
        new_length=1000,  # +900 bytes, which is above the threshold
    )
    mock_redis_client.blpop.side_effect = [
        (config.REDIS_INPUT_LIST, event_data),
        KeyboardInterrupt,
    ]

    # Act
    with pytest.raises(KeyboardInterrupt):
        run_process()

    # Assert
    mock_redis_client.lpush.assert_any_call(config.VANDALISM_FEED_LIST, mocker.ANY)
    pushed_data_str = mock_redis_client.lpush.call_args.args[1]
    pushed_data = json.loads(pushed_data_str)

    assert pushed_data["is_vandalism"] is True
    assert "Unusually large first edit" in pushed_data["vandalism_reasons"][0]


def test_normal_edit_is_not_flagged(mock_redis_client, mocker):
    """
    Tests that a normal, benign edit is NOT flagged as vandalism.
    """
    # Arrange
    event_data = create_mock_edit_event(comment="minor grammar fix")
    mock_redis_client.blpop.side_effect = [
        (config.REDIS_INPUT_LIST, event_data),
        KeyboardInterrupt,
    ]

    # Act
    with pytest.raises(KeyboardInterrupt):
        run_process()

    # Assert: Check that the event was pushed to the LIVE feed
    mock_redis_client.lpush.assert_any_call(config.LIVE_FEED_LIST, mocker.ANY)

    # Assert: Check that the event was NOT pushed to the VANDALISM feed
    # We can do this by checking the call arguments for every lpush call
    for call in mock_redis_client.lpush.call_args_list:
        # The first argument of the call is the list name
        assert call.args[0] != config.VANDALISM_FEED_LIST
