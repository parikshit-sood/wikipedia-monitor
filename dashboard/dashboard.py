import streamlit as st
import redis
import json
import time
import sys
import os

# Add the parent directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Redis configuration
try:
    from dashboard import config
except ImportError:
    # If running from dashboard directory directly
    import config

# Page configuration
st.set_page_config(page_title="Real-Time Wikipedia Monitor", layout="wide")


# Connect to Redis
@st.cache_resource(ttl=30)
def get_redis_connection():
    print("Connecting to Redis for the dashboard...")
    return redis.Redis(
        host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True
    )


redis_client = get_redis_connection()

# UI Layout
st.title("Real-Time Wikipedia Edits Monitor")
st.markdown(
    "This dashboard conencts to a Redis cache to display data processed from Wikipedia's real-time event stream."
)

# Create two columns for main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Live Edit Feed")
    st.caption("Showing the last 20 edits received.")
    live_feed_placeholder = st.empty()

with col2:
    st.header("Vandalism Alerts")
    st.caption("Edits flagged as potential vandalism by the processing engine.")
    vandalism_alert_placeholder = st.empty()

# Refresh the dashboard forever
while True:
    # Update Live Feed Display
    live_edits_raw = redis_client.lrange(
        config.LIVE_FEED_LIST, 0, 19
    )  # Fetch latest 20
    live_edits = [json.loads(e) for e in live_edits_raw]

    with live_feed_placeholder.container():
        if not live_edits:
            st.info("Waiting for new edits...")
        else:
            for edit in live_edits:
                edit_size = edit.get("length", {}).get("new", 0) - edit.get(
                    "length", {}
                ).get("old", 0)

                user_type = ""
                if edit.get("user_is_anonymous"):
                    user_type = " (Anonymous)"
                if edit.get("user_is_bot"):
                    user_type = " (Bot)"

                summary = edit.get("comment", "No summary provided.")
                st.markdown(
                    f"""
                    **{edit.get("title")}** `{edit_size} bytes`
                    > {summary}
                    *by **{edit.get("performer", {}).get("user_text")}{user_type}***
                    [Link]({edit.get("meta", {}).get("uri")})
                    """
                )
                st.divider()

    # Update Vandalism Alerts Display
    vandalism_alerts_raw = redis_client.lrange(config.VANDALISM_FEED_LIST, 0, 49)
    vandalism_alerts = [json.loads(v) for v in vandalism_alerts_raw]

    with vandalism_alert_placeholder.container():
        if not vandalism_alerts:
            st.success("No vandalism detected recently.")
        else:
            for alert in vandalism_alerts:
                with st.container(border=True):
                    st.error(f"**{alert.get('title')}**")
                    st.markdown(
                        f"**Reason(s):** {', '.join(alert.get('vandalism_reasons', ['Unknown']))}"
                    )
                    st.write(f"**User:** {alert.get('performer', {}).get('user_text')}")
                    st.link_button("View Edit", alert.get("meta", {}).get("uri"))

    # Refresh dashboard every 3 seconds
    time.sleep(3)
