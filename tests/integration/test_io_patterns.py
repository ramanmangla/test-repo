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

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest

from agents.agentic_rag_vertexai_search.app.agent import agent as vais_agent
from agents.crewai_coding_crew.app.agent import agent as crewai_agent
from agents.langgraph_base_react.app.agent import agent as langgraph_agent

# Define the list of agents to test
AGENTS_TO_TEST = [
    pytest.param(
        langgraph_agent,
        "What's the weather in NY?",  ## Add a question that can trigger a tool call
        id="langgraph_agent",
    ),
    pytest.param(
        crewai_agent,
        "Write a function that calculates the factorial of a number.",
        id="crewai_agent",
    ),
    pytest.param(
        vais_agent,
        "How to split a string with pattern 'alphabet/alphabet' and not split 'number/number' in same string",
        id="vais_agent",
    ),
]


@pytest.mark.parametrize("agent,test_message", AGENTS_TO_TEST)
@patch(
    "agents.agentic_rag_vertexai_search.app.agent.retrieve_docs.func",
    return_value=("dummy content", [{"page_content": "Test document content"}]),
)
def test_agent_stream(
    mock_retrieve: Any, agent: Callable[..., Any], test_message: str
) -> None:
    """
    Integration test for the agent stream functionality.
    Tests that all agent agents return valid streaming responses.

    Args:
        mock_retrieve: The mocked retrieve_docs function
        agent: The agent callable to test
        test_message: Test message specific to this agent
    """
    input_dict = {
        "messages": [
            {"type": "human", "content": "Hi"},
            {"type": "ai", "content": "Hi there!"},
            {"type": "human", "content": test_message},
        ]
    }

    events = [
        message
        for message, _ in agent.stream(input_dict, stream_mode="messages")  # type: ignore[attr-defined]
    ]

    # Verify we get a reasonable number of messages
    assert len(events) > 0, "Expected at least one message"

    # First message should be an AI message
    assert events[0].type == "AIMessageChunk"

    # At least one message should have content
    has_content = False
    for event in events:
        if hasattr(event, "content") and event.content:
            has_content = True
            break
    assert has_content, "Expected at least one message with content"
