# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
{% if "adk" in cookiecutter.tags %}
import logging
import os
from collections.abc import Generator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.events.event import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.cloud import logging as google_cloud_logging

from app.agent import agent
from app.utils.tracing import CloudTraceLoggingSpanExporter
from app.utils.typing import Config, Feedback, InputChat
{% else %}
import logging
import os
from collections.abc import Generator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse
from google.cloud import logging as google_cloud_logging
from langchain_core.runnables import RunnableConfig
from traceloop.sdk import Instruments, Traceloop

from app.agent import agent
from app.utils.tracing import CloudTraceLoggingSpanExporter
from app.utils.typing import Feedback, InputChat, Request, dumps, ensure_valid_config
{% endif %}

# Initialize FastAPI app and logging
app = FastAPI(
    title="{{cookiecutter.project_name}}",
    description="API for interacting with the Agent {{cookiecutter.project_name}}",
)
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
{% if "adk" in cookiecutter.tags %}
provider = TracerProvider()
processor = export.BatchSpanProcessor(
    CloudTraceLoggingSpanExporter()
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
{% else %}
# Initialize Telemetry
try:
    Traceloop.init(
        app_name=app.title,
        disable_batch=False,
        exporter=CloudTraceLoggingSpanExporter(),
        instruments={Instruments.LANGCHAIN, Instruments.CREW},
    )
except Exception as e:
    logging.error("Failed to initialize Telemetry: %s", str(e))


def set_tracing_properties(config: RunnableConfig) -> None:
    """Sets tracing association properties for the current request.

    Args:
        config: Optional RunnableConfig containing request metadata
    """
    Traceloop.set_association_properties(
        {
            "log_type": "tracing",
            "run_id": str(config.get("run_id", "None")),
            "user_id": config["metadata"].pop("user_id", "None"),
            "session_id": config["metadata"].pop("session_id", "None"),
            "commit_sha": os.environ.get("COMMIT_SHA", "None"),
        }
    )
{% endif %}

def stream_messages(
    input: InputChat,
{% if "adk" in cookiecutter.tags %}
    config: Config | None = None,
{% else %}
    config: RunnableConfig | None = None,
{% endif %}
) -> Generator[str, None, None]:
    """Stream events in response to an input chat.

    Args:
        input: The input chat messages
        config: Optional configuration for the agent

    Yields:
        JSON serialized event data
    """
{% if "adk" in cookiecutter.tags %}
        # Set up stateless session service
        session_service = InMemorySessionService()
        session = session_service.create_session(
            app_name=self.app_name,
            user_id=validated_config.metadata.user_id,
            session_id=validated_config.metadata.session_id,
        )

        # Append each historical event to the session
        for event in input_chat.messages[:-1]:
            session_service.append_event(session=session, event=event)
        new_message = input_chat.messages[-1].content

        # Initialize runner with the agent
        runner = Runner(
            app_name=self.app_name,
            agent=self.root_agent,
            session_service=session_service,
        )

        # Stream responses
        for event in runner.run(
            user_id=validated_config.metadata.user_id,
            session_id=validated_config.metadata.session_id,
            new_message=new_message,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        ):
            yield event.model_dump(mode="json")
{% else %}
    config = ensure_valid_config(config=config)
    set_tracing_properties(config)
    input_dict = input.model_dump()

    for data in agent.stream(input_dict, config=config, stream_mode="messages"):
        yield dumps(data) + "\n"
{% endif %}

# Routes
@app.get("/", response_class=RedirectResponse)
def redirect_root_to_docs() -> RedirectResponse:
    """Redirect the root URL to the API documentation."""
    return RedirectResponse(url="/docs")


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


@app.post("/stream_messages")
def stream_chat_events(request: Request) -> StreamingResponse:
    """Stream chat events in response to an input request.

    Args:
        request: The chat request containing input and config

    Returns:
        Streaming response of chat events
    """
    return StreamingResponse(
        stream_messages(input=request.input, config=request.config),
        media_type="text/event-stream",
    )


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
