# Data Ingestion Pipeline for RAG

The Agent Starter Pack simplifies incorporating data ingestion into your agent projects. This is especially useful for agents requiring document processing and retrieval, such as Retrieval Augmented Generation (RAG) applications.

## Overview

Data ingestion automates:

-   Loading data from various sources.
-   Processing and chunking documents.
-   Generating embeddings with Vertex AI.
-   Storing processed data in Vertex AI Search.
-   Scheduling periodic data updates.

## When to Include Data Ingestion

Consider data ingestion if:

-   Your agent needs to search or reference extensive documentation.
-   You're developing a RAG-based application.
-   Your agent's knowledge base requires periodic updates.
-   You want to keep your agent's content fresh and searchable.

## Usage

### Project Creation

Include data ingestion during project creation in two ways:

1.  **Automatic Inclusion**: Some agents (e.g., `agentic_rag_vertexai_search`) automatically include it due to its nature.

2.  **Optional Inclusion**: For other agents, add it using the `--include-data-ingestion` flag:

    ```bash
    agent-starter-pack create my-agent-project --include-data-ingestion
    ```

### Infrastructure Setup

The data pipeline automatically configures:

-   Vertex AI Search datastores.
-   Necessary service accounts and permissions.
-   Storage buckets for pipeline artifacts.
-   BigQuery datasets (if applicable).

## Getting Started

1.  Create your project with data ingestion:

    ```bash
    agent-starter-pack create my-project --include-data-ingestion
    ```

2.  Follow the setup in the generated `data_ingestion/README.md`. Deploy the Terraform infrastructure (at least in your development project) before running the data pipeline.

## Learn More

-   [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction) for pipeline management.
-   [Vertex AI Search documentation](https://cloud.google.com/generative-ai-app-builder/docs/enterprise-search-introduction) for search capabilities.
