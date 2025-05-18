import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any, Literal

import backoff
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import logging as google_cloud_logging
from google.genai import types
from google.genai.types import LiveServerToolCall
from pydantic import BaseModel
from websockets.exceptions import ConnectionClosedError

from app.agent import MODEL_ID, genai_client, live_connect_config, tool_functions

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
logging.basicConfig(level=logging.INFO)


class GeminiSession:
    def __init__(
        self, session: Any, websocket: WebSocket, tool_functions: dict[str, Callable]
    ) -> None:
        """Initialize the Gemini session."""
        self.session = session
        self.websocket = websocket
        self.run_id = "n/a"
        self.user_id = "n/a"
        self.tool_functions = tool_functions
        # Track when we last received output from Gemini
        self.last_model_message_time = asyncio.get_event_loop().time()
        # Track the last audio token count
        self.last_audio_token_count = 0

    async def receive_from_client(self) -> None:
        """Listen for and process messages from the client."""
        # Create a task for the timer
        timer_task = asyncio.create_task(self.send_continue_prompt())
        
        try:
            while True:
                try:
                    data = await self.websocket.receive_json()
                    if isinstance(data, dict) and (
                        "realtimeInput" in data or "clientContent" in data
                    ):
                        await self.session._ws.send(json.dumps(data))
                    elif "setup" in data:
                        self.run_id = data["setup"]["run_id"]
                        self.user_id = data["setup"]["user_id"]
                        logger.log_struct(
                            {**data["setup"], "type": "setup"}, severity="INFO"
                        )
                    else:
                        logging.warning(f"Received unexpected input from client: {data}")
                except ConnectionClosedError as e:
                    logging.warning(f"Client {self.user_id} closed connection: {e}")
                    break
                except Exception as e:
                    logging.error(f"Error receiving from client {self.user_id}: {e!s}")
                    break
        finally:
            # Cancel the timer task when the connection closes
            timer_task.cancel()

    async def send_continue_prompt(self):
        """Sends a 'continue' message to Gemini only if it hasn't sent data recently.
        Wait time is dynamically calculated based on audio token count."""
        continue_message = {
            'clientContent': {
                'turns': [
                    {
                        'role': 'user', 
                        'parts': [
                            {'text': 'continue commenting according to your system instructions!'}
                        ]
                    }
                ], 
                'turnComplete': True
            }
        }
        
        while True:
            try:
                # Very aggressive dynamic waiting - 0.25 seconds per token
                # This means a 225 token response would wait ~56 seconds plus base time
                base_wait_time = 1  # Minimum base wait
                wait_time = base_wait_time + (self.last_audio_token_count * 0.040)
                
                logging.info(f"Waiting {wait_time:.1f} seconds based on {self.last_audio_token_count} audio tokens")
                await asyncio.sleep(wait_time)
                
                current_time = asyncio.get_event_loop().time()
                time_since_last_message = current_time - self.last_model_message_time
                
                if hasattr(self, 'session') and hasattr(self.session, '_ws'):
                    if time_since_last_message > wait_time:
                        logging.info("Sending continue prompt to Gemini")
                        await self.session._ws.send(json.dumps(continue_message))
                        # Reset audio token count after sending continue
                        self.last_audio_token_count = 0
                    else:
                        logging.info("Skipping continue prompt, model is already active")
            except asyncio.CancelledError:
                # Handle cancellation when the main task ends
                break
            except Exception as e:
                logging.error(f"Error sending continue prompt: {e!s}")

    async def receive_from_gemini(self) -> None:
        """Listen for and process messages from Gemini."""
        while result := await self.session._ws.recv(decode=False):
            # Update timestamp whenever we receive any message from Gemini
            self.last_model_message_time = asyncio.get_event_loop().time()
            
            await self.websocket.send_bytes(result)
            raw_message = json.loads(result)
            
            # Extract audio token count if available in the response metadata
            if "usageMetadata" in raw_message:
                candidates_tokens_details = raw_message["usageMetadata"].get("candidatesTokensDetails", [])
                for token_detail in candidates_tokens_details:
                    if token_detail.get("modality") == "AUDIO":
                        self.last_audio_token_count = token_detail.get("tokenCount", 0)
                        logging.info(f"Detected audio response with {self.last_audio_token_count} tokens")
                        logging.info(f"Next continue prompt will wait ~{1 + (self.last_audio_token_count * 0.040):.1f} seconds")
            
            if "toolCall" in raw_message:
                message = types.LiveServerMessage.model_validate(raw_message)
                tool_call = LiveServerToolCall.model_validate(message.tool_call)
                asyncio.create_task(self._handle_tool_call(self.session, tool_call))

    def _get_func(self, action_label: str | None) -> Callable | None:
        """Get the tool function for a given action label."""
        if action_label is None or action_label == "":
            return None
        return self.tool_functions.get(action_label)


    async def _handle_tool_call(
        self, session: Any, tool_call: LiveServerToolCall
    ) -> None:
        """Process tool calls from Gemini and send back responses."""
        if tool_call.function_calls is None:
            logging.debug("No function calls in tool_call")
            return

        for fc in tool_call.function_calls:
            logging.debug(f"Calling tool function: {fc.name} with args: {fc.args}")
            func = self._get_func(fc.name)
            if func is None:
                logging.error(f"Function {fc.name} not found")
                continue
            args = fc.args if fc.args is not None else {}

            # Handle both async and sync functions appropriately
            if asyncio.iscoroutinefunction(func):
                # Function is already async
                response = await func(**args)
            else:
                # Run sync function in a thread pool to avoid blocking
                response = await asyncio.to_thread(func, **args)

            tool_response = types.LiveClientToolResponse(
                function_responses=[
                    types.FunctionResponse(name=fc.name, id=fc.id, response=response)
                ]
            )
            logging.debug(f"Tool response: {tool_response}")
            await session.send(input=tool_response)



def get_connect_and_run_callable(websocket: WebSocket) -> Callable:
    """Create a callable that handles Gemini connection with retry logic.

    Args:
        websocket: The client websocket connection

    Returns:
        Callable: An async function that establishes and manages the Gemini connection
    """

    async def on_backoff(details: backoff._typing.Details) -> None:
        await websocket.send_json(
            {
                "status": f"Model connection error, retrying in {details['wait']} seconds..."
            }
        )

    @backoff.on_exception(
        backoff.expo, ConnectionClosedError, max_tries=10, on_backoff=on_backoff
    )
    async def connect_and_run() -> None:
        async with genai_client.aio.live.connect(
            model=MODEL_ID, config=live_connect_config
        ) as session:
            await websocket.send_json({"status": "Backend is ready for conversation"})
            gemini_session = GeminiSession(
                session=session, websocket=websocket, tool_functions=tool_functions
            )
            logging.info("Starting bidirectional communication")
            await asyncio.gather(
                gemini_session.receive_from_client(),
                gemini_session.receive_from_gemini(),
            )

    return connect_and_run


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle new websocket connections."""
    await websocket.accept()
    connect_and_run = get_connect_and_run_callable(websocket)
    await connect_and_run()


class Feedback(BaseModel):
    """Represents feedback for a conversation."""

    score: int | float
    text: str | None = ""
    run_id: str
    user_id: str | None
    log_type: Literal["feedback"] = "feedback"


@app.post("/feedback")
async def collect_feedback(feedback_dict: Feedback) -> None:
    """Collect and log feedback."""
    feedback_data = feedback_dict.model_dump()
    logger.log_struct(feedback_data, severity="INFO")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")