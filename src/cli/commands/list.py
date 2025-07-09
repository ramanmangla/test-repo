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

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console
from rich.table import Table

from ..utils.logging import handle_cli_error
from ..utils.template import get_available_agents

console = Console()


@click.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(["local", "adk"]),
    default="local",
    help="Source of templates to list (local or adk-samples)",
)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@handle_cli_error
def list_templates(source: str, debug: bool) -> None:
    """List available agent templates."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        console.print("> Debug mode enabled")
        logging.debug("Starting list command in debug mode")

    if source == "local":
        list_local_templates()
    elif source == "adk":
        list_adk_templates()


def list_local_templates() -> None:
    """List locally available templates."""
    console.print("\n[bold blue]Local Agent Templates[/]")
    console.print("These templates are available locally:")

    agents = get_available_agents()

    if not agents:
        console.print("No local templates found.")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Number", style="dim", width=8)
    table.add_column("Name", style="bold")
    table.add_column("Description")

    for num, agent in agents.items():
        table.add_row(str(num), agent["name"], agent["description"])

    console.print(table)


def list_adk_templates() -> None:
    """List templates from adk-samples repository."""
    console.print("\n[bold blue]ADK Samples Templates[/]")
    console.print("Templates available from google/adk-samples:")

    try:
        templates = fetch_adk_templates()

        if not templates:
            console.print("No ADK templates found or unable to access repository.")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Shortcut", style="dim", width=20)
        table.add_column("Name", style="bold")
        table.add_column("Description")

        for template in templates:
            shortcut = f"adk@{template['name']}"
            table.add_row(shortcut, template["display_name"], template["description"])

        console.print(table)
        console.print(
            "\n[dim]Usage: agent-starter-pack create <project-name> --agent adk@<template-name>[/]"
        )

    except Exception as e:
        console.print(f"[red]Error fetching ADK templates: {e}[/]")
        console.print(
            "[yellow]You can still use ADK templates with the format: adk@<template-name>[/]"
        )


def fetch_adk_templates() -> list[dict[str, Any]]:
    """Fetch available templates from adk-samples repository."""
    templates = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Clone the adk-samples repository
            clone_cmd = [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "main",
                "https://github.com/google/adk-samples",
                str(temp_path / "repo"),
            ]

            result = subprocess.run(
                clone_cmd, capture_output=True, text=True, check=True
            )

            if result.returncode != 0:
                logging.error(f"Failed to clone adk-samples: {result.stderr}")
                return []

            # Look for templates in python/agents directory
            agents_dir = temp_path / "repo" / "python" / "agents"

            if not agents_dir.exists():
                logging.warning(f"Agents directory not found: {agents_dir}")
                return []

            # Scan for template configs
            for agent_dir in agents_dir.iterdir():
                if not agent_dir.is_dir():
                    continue

                # Look for template config
                config_path = agent_dir / ".template" / "template_config.yaml"
                if not config_path.exists():
                    # Try legacy location
                    config_path = agent_dir / ".templateconfig.yaml"

                if config_path.exists():
                    try:
                        with open(config_path) as f:
                            config = yaml.safe_load(f)

                        template_info = {
                            "name": agent_dir.name,
                            "display_name": config.get("name", agent_dir.name),
                            "description": config.get(
                                "description", "No description available"
                            ),
                            "example_question": config.get("example_question", ""),
                        }
                        templates.append(template_info)

                    except Exception as e:
                        logging.warning(
                            f"Error reading config for {agent_dir.name}: {e}"
                        )
                        continue

        except subprocess.CalledProcessError as e:
            logging.error(f"Git command failed: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error fetching templates: {e}")
            return []

    return sorted(templates, key=lambda x: x["name"])
