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
import pathlib
import subprocess

import click
from click.core import ParameterSource
from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from ..utils.gcp import verify_credentials, verify_vertex_connection
from ..utils.logging import handle_cli_error
from ..utils.template import (
    get_available_agents,
    get_template_path,
    process_template,
    prompt_data_ingestion,
    prompt_deployment_target,
)

console = Console()


@click.command()
@click.pass_context
@click.argument("project_name")
@click.option("--agent", "-a", help="agent name or number to use")
@click.option(
    "--deployment-target",
    "-d",
    type=click.Choice(["agent_engine", "cloud_run"]),
    help="Deployment target name",
)
@click.option(
    "--include-data-ingestion", "-i", is_flag=True, help="Include data pipeline"
)
@click.option("--gcp-account", help="GCP service account email")
@click.option("--gcp-project", help="GCP project ID")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory for the project (default: current directory)",
)
@click.option(
    "--auto-approve", is_flag=True, help="Skip credential confirmation prompts"
)
@click.option(
    "--region",
    help="GCP region for deployment (default: us-central1)",
    default="us-central1",
)
@click.option(
    "--skip-checks",
    is_flag=True,
    help="Skip verification checks for uv, GCP and Vertex AI",
    default=False,
)
@handle_cli_error
def create(
    ctx: click.Context,
    project_name: str,
    agent: str | None,
    deployment_target: str | None,
    include_data_ingestion: bool,
    gcp_account: str | None,
    gcp_project: str | None,
    debug: bool,
    output_dir: str | None,
    auto_approve: bool,
    region: str,
    skip_checks: bool,
) -> None:
    """Create GCP-based AI agent projects from templates."""
    try:
        # Display welcome banner
        console.print("\n=== GCP Agent Starter Pack :rocket:===", style="bold blue")
        console.print("Welcome to the Agent Starter Pack!")
        console.print(
            "This tool will help you create an end-to-end production-ready AI agent in GCP!\n"
        )

        # Setup debug logging if enabled
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            console.print("> Debug mode enabled")
            logging.debug("Starting CLI in debug mode")

        # Convert output_dir to Path if provided, otherwise use current directory
        destination_dir = pathlib.Path(output_dir) if output_dir else pathlib.Path.cwd()
        destination_dir = destination_dir.resolve()  # Convert to absolute path

        # Check if project would exist in output directory
        project_path = destination_dir / project_name
        if project_path.exists():
            console.print(
                f"Error: Project directory '{project_path}' already exists",
                style="bold red",
            )
            return

        # Agent selection
        selected_agent = None
        if agent:
            agents = get_available_agents()
            # First check if it's a valid agent name
            if any(p["name"] == agent for p in agents.values()):
                selected_agent = agent
            else:
                # Try numeric agent selection if input is a number
                try:
                    agent_num = int(agent)
                    if agent_num in agents:
                        selected_agent = agents[agent_num]["name"]
                    else:
                        raise ValueError(f"Invalid agent number: {agent_num}")
                except ValueError as err:
                    raise ValueError(f"Invalid agent name or number: {agent}") from err

        final_agent = (
            selected_agent
            if selected_agent
            else display_agent_selection(deployment_target)
        )
        if debug:
            logging.debug(f"Selected agent: {agent}")

        # Deployment target selection
        final_deployment = (
            deployment_target
            if deployment_target
            else prompt_deployment_target(final_agent)
        )
        if debug:
            logging.debug(f"Selected deployment target: {final_deployment}")

        # Data pipeline selection
        include_data_ingestion = include_data_ingestion or prompt_data_ingestion(final_agent)
        if debug:
            logging.debug(f"Include data pipeline: {include_data_ingestion}")
        # Region confirmation (if not explicitly passed)
        if not auto_approve and ctx.get_parameter_source("region") != ParameterSource.COMMANDLINE:
            region = prompt_region_confirmation(region)
        if debug:
            logging.debug(f"Selected region: {region}")

        # GCP Setup
        with console.status("[bold blue]Setting up GCP environment...", spinner="dots"):
            if debug:
                logging.debug("Setting up GCP...")

        # Handle GCP credentials
        if gcp_account and gcp_project:
            try:
                subprocess.run(
                    ["gcloud", "config", "set", "account", gcp_account], check=True
                )
                subprocess.run(
                    ["gcloud", "config", "set", "project", gcp_project], check=True
                )
                subprocess.run(
                    [
                        "gcloud",
                        "auth",
                        "application-default",
                        "set-quota-project",
                        gcp_project,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                console.print(f"Error setting GCP credentials: {e!s}", style="bold red")
                raise

        if not skip_checks:
            # Verify GCP credentials
            if debug:
                logging.debug("Verifying GCP credentials...")
            creds_info = verify_credentials()

            if not auto_approve:
                change_creds = (
                    Prompt.ask(
                        f"\n> You are logged in with account '{creds_info['account']}' "
                        f"and using project '{creds_info['project']}'. "
                        "Do you wish to change this?",
                        choices=["y", "n"],
                        default="n",
                    ).lower()
                    == "y"
                )

                if change_creds:
                    handle_credential_change()
            else:
                console.print(
                    f"\n> Using account '{creds_info['account']}' "
                    f"with project '{creds_info['project']}'"
                )

            # Check for uv installation
            console.print("> Checking for uv installation...")
            check_and_install_uv()
        else:
            if debug:
                logging.debug("Skipping verification checks due to --skip-checks flag")
            console.print("> Skipping verification checks", style="yellow")
            # Set a default creds_info when skipping checks
            creds_info = {"project": gcp_project} if gcp_project else {"project": "unknown"}

        console.print("> Testing GCP and Vertex AI Connection...")
        try:
            verify_vertex_connection(
                project_id=creds_info["project"],
                location=region,
            )
            console.print(
                f"> ✓ Successfully verified connection to Vertex AI in project {creds_info['project']}"
            )
        except Exception as e:
            console.print(
                f"> ✗ Failed to connect to Vertex AI: {e!s}", style="bold red"
            )
            raise

        # Process template
        template_path = get_template_path(final_agent, debug=debug)
        if debug:
            logging.debug(f"Template path: {template_path}")
            logging.debug(f"Processing template for project: {project_name}")

        # Create output directory if it doesn't exist
        if not destination_dir.exists():
            destination_dir.mkdir(parents=True)

        if debug:
            logging.debug(f"Output directory: {destination_dir}")

        process_template(
            final_agent,
            template_path,
            project_name,
            deployment_target=final_deployment,
            include_data_ingestion=include_data_ingestion,
            output_dir=destination_dir,
        )

        project_path = destination_dir / project_name
        console.print("\n> 👍 Done. Execute the following command to get started:")
        if output_dir:
            # If output_dir was specified, use the absolute path
            console.print(f"[bold bright_green]cd {project_path} && make install && make playground[/]")
        else:
            # If no output_dir specified, just use project name
            console.print(f"[bold bright_green]cd {project_name} && make install && make playground[/]")

        # Replace region in all files if a different region was specified
        if region != "us-central1":
            replace_region_in_files(project_path, region, debug=debug)
    except Exception:
        if debug:
            logging.exception(
                "An error occurred:"
            )  # This will print the full stack trace
        raise


def prompt_region_confirmation(default_region: str = "us-central1") -> str:
    """Prompt user to confirm or change the default region."""
    console.print(f"\n> Default GCP region is '{default_region}'")
    new_region = Prompt.ask(
        "Enter desired GCP region (leave blank for default)",
        default="",
        show_default=False,
    )

    return new_region if new_region else default_region


def display_agent_selection(deployment_target: str | None = None) -> str:
    """Display available agents and prompt for selection."""
    agents = get_available_agents(deployment_target=deployment_target)

    if not agents:
        if deployment_target:
            raise click.ClickException(
                f"No agents available for deployment target '{deployment_target}'"
            )
        raise click.ClickException("No valid agents found")

    console.print("\n> Please select a agent to get started:")
    for num, agent in agents.items():
        console.print(
            f"{num}. [bold]{agent['name']}[/] - [dim]{agent['description']}[/]"
        )

    choice = IntPrompt.ask(
        "\nEnter the number of your template choice", default=1, show_default=True
    )

    if choice not in agents:
        raise ValueError(f"Invalid agent selection: {choice}")

    return agents[choice]["name"]


def handle_credential_change() -> None:
    """Handle the process of changing GCP credentials."""
    try:
        console.print("\n> Initiating new login...")
        subprocess.run(["gcloud", "auth", "login", "--update-adc"], check=True)
        console.print("> Login successful. Verifying new credentials...")

        # Re-verify credentials after login
        new_creds_info = verify_credentials()

        # Prompt for project change
        change_project = (
            Prompt.ask(
                f"\n> You are now logged in with account '{new_creds_info['account']}'. "
                f"Current project is '{new_creds_info['project']}'. "
                "Do you wish to change the project?",
                choices=["y", "n"],
                default="n",
            ).lower()
            == "y"
        )

        if change_project:
            handle_project_change()

    except subprocess.CalledProcessError as e:
        console.print(
            "\n> Error during login process. Please try again.", style="bold red"
        )
        logging.debug(f"Login error: {e!s}")
        raise
    except Exception as e:
        console.print(f"\n> Unexpected error: {e!s}", style="bold red")
        logging.debug(f"Unexpected error during login: {e!s}")
        raise


def handle_project_change() -> None:
    """Handle the process of changing GCP project."""
    try:
        # Prompt for new project ID
        new_project = Prompt.ask("\n> Enter the new project ID")

        console.print(f"\n> Setting project to {new_project}...")
        subprocess.run(["gcloud", "config", "set", "project", new_project], check=True)

        console.print("> Setting application default quota project...")
        subprocess.run(
            ["gcloud", "auth", "application-default", "set-quota-project", new_project],
            check=True,
        )

        console.print(f"> Successfully switched to project: {new_project}")

        # Re-verify credentials one final time
        final_creds_info = verify_credentials()
        console.print(
            f"\n> Now using account '{final_creds_info['account']}' "
            f"with project '{final_creds_info['project']}'"
        )

    except subprocess.CalledProcessError as e:
        console.print(
            "\n> Error while changing project. Please verify the project ID and try again.",
            style="bold red",
        )
        logging.debug(f"Project change error: {e!s}")
        raise


def replace_region_in_files(
    project_path: pathlib.Path, new_region: str, debug: bool = False
) -> None:
    """Replace all instances of 'us-central1' with the specified region in project files.
    Also handles vertex_ai_search region mapping.

    Args:
        project_path: Path to the project directory
        new_region: The new region to use
        debug: Whether to enable debug logging
    """
    if debug:
        logging.debug(
            f"Replacing region 'us-central1' with '{new_region}' in {project_path}"
        )

    # Define allowed file extensions
    allowed_extensions = {".md", ".py", ".tfvars", ".yaml", ".tf", ".yml"}

    # Skip directories that shouldn't be modified
    skip_dirs = {".git", "__pycache__", "venv", ".venv", "node_modules"}

    # Determine data_store_region region value
    if new_region.startswith("us"):
        data_store_region = "us"
    elif new_region.startswith("europe"):
        data_store_region = "eu"
    else:
        data_store_region = "global"

    for file_path in project_path.rglob("*"):
        # Skip directories and files with unwanted extensions
        if (
            file_path.is_dir()
            or any(skip_dir in file_path.parts for skip_dir in skip_dirs)
            or file_path.suffix not in allowed_extensions
        ):
            continue

        try:
            content = file_path.read_text()
            modified = False

            # Replace standard region references
            if "us-central1" in content:
                if debug:
                    logging.debug(f"Replacing region in {file_path}")
                content = content.replace("us-central1", new_region)
                modified = True

            # Replace data_store_region region if present (all variants)
            if 'data_store_region = "us"' in content:
                if debug:
                    logging.debug(f"Replacing vertex_ai_search region in {file_path}")
                content = content.replace(
                    'data_store_region = "us"',
                    f'data_store_region = "{data_store_region}"',
                )
                modified = True
            elif 'data_store_region="us"' in content:
                if debug:
                    logging.debug(f"Replacing data_store_region in {file_path}")
                content = content.replace(
                    'data_store_region="us"', f'data_store_region="{data_store_region}"'
                )
                modified = True
            elif "_DATA_STORE_REGION: us" in content:
                if debug:
                    logging.debug(f"Replacing _DATA_STORE_REGION in {file_path}")
                content = content.replace(
                    "_DATA_STORE_REGION: us", f"_DATA_STORE_REGION: {data_store_region}"
                )
                modified = True

            if modified:
                file_path.write_text(content)

        except UnicodeDecodeError:
            # Skip files that can't be read as text
            continue


def check_and_install_uv() -> None:
    """Check if uv is installed and install it if not present."""
    try:
        # Use shell=True for Windows compatibility and add timeout
        process = subprocess.run(
            "uv --version",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if process.returncode == 0:
            logging.debug("uv is already installed")
            return
        else:
            console.print("> uv command failed", style="yellow")
    except subprocess.TimeoutExpired:
        console.print("> uv version check timed out", style="yellow")
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("> uv is not installed", style="yellow")

    console.print(
        "\n> uv is required for the template to work. You can install it in several ways:"
        "\n 1. Automatically install uv now"
        "\n 2. Manual installation from: https://docs.astral.sh/uv/getting-started/installation"
        "\n    This includes other options e.g PyPI (pip/pipx), Homebrew, Docker.."
    )

    install_choice = Prompt.ask(
        "\n> Would you like to install uv automatically now?",
        choices=["y", "n"],
        default="y",
    )
    if install_choice.lower() == "y":
        console.print("> Installing uv...", style="yellow")
        try:
            install_command = "curl -LsSf https://astral.sh/uv/install.sh | sh"
            # Add timeout to installation process as well
            subprocess.run(
                install_command,
                shell=True,
                check=True,
                timeout=60  # Give installation more time
            )
            console.print("> uv installed successfully!", style="green")
        except subprocess.TimeoutExpired:
            console.print("> uv installation timed out", style="bold red")
            raise
        except subprocess.CalledProcessError as e:
            console.print("> Failed to install uv", style="bold red")
            logging.debug(f"uv installation error: {e!s}")
            console.print(
                "> Please install uv manually using one of the methods listed above",
                style="yellow",
            )
            raise
    else:
        console.print(
            "> Please install uv manually using one of the methods listed above and try again",
            style="yellow",
        )
        raise click.Abort() from None
