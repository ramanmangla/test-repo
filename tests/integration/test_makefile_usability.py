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
import pathlib
import re
import subprocess
from datetime import datetime

from rich.console import Console

from tests.integration.utils import run_command
from tests.utils.get_agents import get_test_combinations_to_run

console = Console()
TARGET_DIR = "target"


def validate_makefile_usability(
    agent: str, deployment_target: str, extra_params: list[str] | None = None
) -> None:
    """Test that the generated Makefile is syntactically valid and usable"""
    timestamp = datetime.now().strftime("%m%d%H%M%S")
    project_name = f"{agent[:8]}-{deployment_target[:5]}-{timestamp}".replace("_", "-")
    project_path = pathlib.Path(TARGET_DIR) / project_name
    region = "us-central1" if agent == "live_api" else "europe-west4"

    try:
        # Create target directory if it doesn't exist
        os.makedirs(TARGET_DIR, exist_ok=True)

        # Template the project
        cmd = [
            "python",
            "-m",
            "src.cli.main",
            "create",
            project_name,
            "--agent",
            agent,
            "--deployment-target",
            deployment_target,
            "--region",
            region,
            "--auto-approve",
            "--skip-checks",
        ]

        # Add any extra parameters
        if extra_params:
            cmd.extend(extra_params)

        run_command(
            cmd,
            pathlib.Path(TARGET_DIR),
            f"Templating {agent} project with {deployment_target}",
        )

        makefile_path = project_path / "Makefile"
        if not makefile_path.exists():
            raise FileNotFoundError(f"Makefile not found at {makefile_path}")

        # Check for unrendered placeholders
        with open(makefile_path) as f:
            content = f.read()
            if "{{" in content or "}}" in content:
                raise ValueError(
                    f"Found unrendered placeholders in Makefile for {agent} with {deployment_target}"
                )

        # Test make syntax validation
        try:
            run_command(
                ["make", "--dry-run", "--print-data-base"],
                project_path,
                "Validating Makefile syntax",
            )
        except subprocess.CalledProcessError as e:
            console.print("[bold red]Makefile syntax validation failed[/]")
            if e.stdout:
                console.print(e.stdout)
            if e.stderr:
                console.print(e.stderr)
            raise ValueError(
                f"Makefile syntax is invalid for {agent} with {deployment_target}"
            ) from e

        makefile_targets = []
        with open(makefile_path) as f:
            makefile_content = f.read()

        # Find all targets using regex - looks for lines that start with word characters followed by :
        # This matches actual targets like "install:", "test:", etc.
        target_pattern = r"^([a-zA-Z0-9_-]+):"
        matches = re.findall(target_pattern, makefile_content, re.MULTILINE)

        # Filter out any unwanted targets
        for target in matches:
            if (
                target
                and not target.startswith(".")
                and "%" not in target  # Skip pattern rules
                and target
                not in ["all", "clean", "distclean"]  # Skip common implicit targets
            ):
                makefile_targets.append(target)

        # Test dry run of each target
        for target in set(makefile_targets):  # Remove duplicates
            try:
                run_command(
                    ["make", "--dry-run", target],
                    project_path,
                    f"Testing dry run for target: {target}",
                )
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]Target '{target}' failed dry run[/]")
                if e.stdout:
                    console.print(e.stdout)
                if e.stderr:
                    console.print(e.stderr)
                raise ValueError(
                    f"Target '{target}' is not valid in Makefile for {agent} with {deployment_target}"
                ) from e

        console.print(
            f"[bold green]✓ Makefile validation passed for {agent} with {deployment_target}[/]"
        )

    except Exception as e:
        console.print(
            f"[bold red]Error validating Makefile for {agent} with {deployment_target}:[/] {e!s}"
        )
        raise


def test_all_makefile_usability() -> None:
    """Test Makefile usability for all template combinations"""
    combinations = get_test_combinations_to_run()

    for agent, deployment_target, extra_params in combinations:
        console.print(
            f"\n[bold cyan]Testing Makefile usability for {agent} with {deployment_target}[/]"
        )
        validate_makefile_usability(agent, deployment_target, extra_params)


if __name__ == "__main__":
    test_all_makefile_usability()
