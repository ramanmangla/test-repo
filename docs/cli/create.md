# CLI Commands

The Agent Starter Pack provides CLI commands to help you create and manage AI agent projects.

## Create Command

The `create` command helps you create new GCP-based AI agent projects from templates.

```bash
agent-starter-pack create PROJECT_NAME [OPTIONS]
```

### Arguments

- `PROJECT_NAME`: Name of the project to create

### Options

The following options will be prompted interactively if not provided:
- `--agent`, `-a`: Agent name or number to use
- `--deployment-target`, `-d`: Deployment target (`agent_engine` or `cloud_run`)
- `--region`: GCP region for deployment (default: us-central1)
- `--gcp-account`: GCP account email
- `--gcp-project`: GCP project ID

Additional options:
- `--include-data-ingestion`, `-i`: Include data pipeline. Some agents e.g `agentic_rag_vertexai_search` will require and include this by default.
- `--debug`: Enable debug logging
- `--output-dir`, `-o`: Output directory for the project (default: current directory)
- `--auto-approve`: Skip credential confirmation prompts
- `--skip-checks`: Skip verification checks for uv and GCP

### Example Usage

```bash
# Create a new project
agent-starter-pack create my-agent-project

# Create with specific agent and deployment target and google cloud region
agent-starter-pack create my-agent-project -a chat_agent -d cloud_run --region europe-west1
```
