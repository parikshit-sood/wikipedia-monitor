# Real-Time Wikipedia Monitor & Vandalism Detection

_A live dashboard monitoring the pulse of global knowledge creation on Wikipedia._

This project is a real-time data engineering pipeline that ingests the live feed of all Wikipedia edits, processes them to detect potential vandalism, and visualizes the stream on a live dashboard. It's designed to showcase a modern, decoupled, and scalable stream-processing architecture.

## Key Features

-   **Live Feed:** Monitors every edit made to Wikipedia across all languages in real-time.
-   **Vandalism Detection:** Uses a heuristic model to flag suspicious edits, such as large-scale deletions by anonymous users or the addition of blacklisted keywords.
-   **Real-Time Dashboard:** A dynamic web interface built with Streamlit that visualizes the live feed and highlights potential vandalism alerts as they happen.
-   **Decoupled Architecture:** Built with independent services for data ingestion, processing, and visualization, ensuring resilience and scalability.
-   **Efficient Cachiing:** Utilizes Redis as a high-speed, in-memory message broker and cache, ensuring low latency between services.

## System Architecture

The project follows a classic, robus stream-processing pattern that separates concerns into distinct services. This decoupling prevents bottlenecks and allows each component to be scaled or maintained independently.

1. **Data Ingestion Service: [ingest/](ingest/):** A persistent Python service that connects to the Wikimedia Server-Sent Events (SSE) stream. It fetches raw edit data and pushes it into a Redis list, acting as a raw data buffer.
2. **Stream Processing Engine [process/](process/):** This core service continuously pulls raw data from Redis. It parses and enriches the data, applies a rules-based model to detect potential vandalism, and then pushes the structure results into separate, capped Redis lists for consumption by the dashboard.
3. **Redis Cache:** An in-memory data store acting as the central nervous system. It serves as a message queue between the ingestion and processing services and a data cache for the dashboard.
4. **Real-Time Dashboard [dashboard/](dashboard/):** A web application that pools the Redis cache every few seconds for processed data and vandalism alerts, displaying them to the user without ever connecting directly to the high-volume data stream.

## Tech Stack

-   **Data Source:** Wikimedia Foundation's real-time SSE Stream
-   **Programming Language:** Python 3
-   **Core Libraries:**
    -   `requests` and `sseclient-py`: For connecting to the SSE data stream
    -   `redis`: For high-speed caching and messaging
-   **Infrastructure:**
    -   **Redis:** In-memory data store and message broker
    -   **Docker:** For running Redis and containerizing services
    -   **Supervisor:** For managing and daemonizing the Python services on a server.

## Getting Started

TODO

## Configuration

TODO

## License

TODO
