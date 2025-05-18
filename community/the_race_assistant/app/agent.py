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

import os

import google
import vertexai
from google import genai
from google.genai import types
from langchain_community.retrievers import WikipediaRetriever

from app.templates import SYSTEM_INSTRUCTION

# Constants
VERTEXAI = os.getenv("VERTEXAI", "true").lower() == "true"
LOCATION = "us-central1"
MODEL_ID = "gemini-2.0-flash-live-preview-04-09"


# Initialize Google Cloud clients
credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=LOCATION)


if VERTEXAI:
    genai_client = genai.Client(project=project_id, location=LOCATION, vertexai=True)
else:
    # API key should be set using GOOGLE_API_KEY environment variable
    genai_client = genai.Client(http_options={"api_version": "v1alpha"})


async def get_wikipedia_info(query: str) -> dict:
    """Retrieves information from Wikipedia.

    Args:
        query: A string containing the search query for Wikipedia.

    Returns:
        A dictionary containing the Wikipedia article content.
    """
    # Limit to 1 document to get the most relevant result quickly for a "fun fact"
    retriever = WikipediaRetriever(load_max_docs=1)
    try:
        docs = retriever.invoke(query)
        if docs:
            # Return the full content of the first document for the model to process
            return {"output": docs[0].page_content[:200]}
        else:
            return {"output": "No Wikipedia information found for the query."}
    except Exception as e:
        # Catch potential exceptions during retrieval (e.g., network issues)
        return {"output": f"An error occurred while searching Wikipedia: {e}"}


# Configure tools available to the agent and live connection
tool_functions = {"get_wikipedia_info": get_wikipedia_info}


live_connect_config = types.LiveConnectConfig(
    response_modalities=[types.Modality.TEXT],
    tools=list(tool_functions.values()),
    # tools=[types.Tool(google_search=types.GoogleSearch())],
    # Change to desired language code (e.g., "es-ES" for Spanish, "fr-FR" for French)
    speech_config=types.SpeechConfig(language_code="en-US"),
    system_instruction=types.Content(parts=[{"text": SYSTEM_INSTRUCTION}]),
    context_window_compression=(
        # Configures compression with default parameters.
        types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(),
        )
    ),
)
