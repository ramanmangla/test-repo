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
MODEL_ID = "gemini-2.0-flash-live-001"


# Initialize Google Cloud clients
credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=LOCATION)


if VERTEXAI:
    genai_client = genai.Client(project=project_id, location=LOCATION, vertexai=True)
else:
    # API key should be set using GOOGLE_API_KEY environment variable
    genai_client = genai.Client(http_options={"api_version": "v1alpha"})


def retrieve_facts(query: str) -> dict:
    """Retrieves relevant facts from Wikipedia for the race commentary."""
    try:
        retriever = WikipediaRetriever(load_max_docs=3) # Limit docs for speed
        docs = retriever.invoke(query)
        # Combine the page content of the retrieved documents
        result = "\n\n".join([doc.page_content for doc in docs])
        return {"output": result}
    except Exception as e:
        # Handle potential errors during retrieval
        return {"output": f"Error retrieving facts: {e}"}


tool_functions = {"retrieve_facts": retrieve_facts}

live_connect_config = types.LiveConnectConfig(
    response_modalities=[types.Modality.AUDIO],
    tools=list(tool_functions.values()),
    # Change to desired language code (e.g., "es-ES" for Spanish, "fr-FR" for French)
    speech_config=types.SpeechConfig(language_code="en-US"),
    system_instruction=types.Content(parts=[{"text": SYSTEM_INSTRUCTION}]),
)
