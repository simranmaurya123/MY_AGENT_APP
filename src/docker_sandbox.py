
import subprocess
import tempfile
import shutil
from pathlib import Path


class DockerSandbox:
    """Execute agent commands inside a restricted Docker container."""

    def __init__(
        self,
        image: str = "agent-sandbox:latest",
        workspace: str | None = None,
        timeout: int = 30,
        memory_limit: str = "512m",
        network: bool = False,
    ):
        self.image = image
        self.workspace = workspace or tempfile.mkdtemp(prefix="agent-")
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.network = network

    def cleanup(self):
        """Remove temporary workspace."""
        shutil.rmtree(self.workspace, ignore_errors=True)

    def execute(self, command: str) -> dict:
        """
        Execute an arbitrary shell command in the sandbox.

        The entire workspace is mounted read-only at /input.
        """

        docker_cmd = [
            "docker", "run",
            "--rm",
            "--user", "1000:1000",
            "--memory", self.memory_limit,
            "--cpus", "1.0",
            "--pids-limit", "100",
            "--read-only",
            "--tmpfs", "/tmp:size=100m",
            "--tmpfs", "/workspace:size=200m",
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
        ]

        print(f"[SANDBOX] Executing command: {command}")

        workspace_path = Path(self.workspace).resolve()

        if workspace_path.exists():
            docker_cmd.extend([
                "--mount",
                f"type=bind,source={workspace_path},target=/input,readonly"
            ])

        if not self.network:
            docker_cmd.extend(["--network", "none"])

        docker_cmd.extend([
            self.image,
            "bash",
            "-c",
            command
        ])

        print("[SANDBOX] Docker command:")
        print(" ".join(map(str, docker_cmd)))

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            return {
                "stdout": result.stdout[-10000:],
                "stderr": result.stderr[-5000:],
                "exit_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout}s",
                "exit_code": -1,
            }

    def execute_with_output(self, script_path: str, output_dir: str) -> dict:
        """
        Execute a Python script in the sandbox.

        Mounts:
            /input/data        -> read-only input files
            /input/temp_script.py -> read-only script
            /output            -> writable output directory

        Generated code should write files to:

            /output/<filename>

        Example:

            merger.write("/output/merged_file.pdf")

        and print:

            CREATED: /output/merged_file.pdf
        """

        import os

        data_dir = os.path.join(self.workspace, "data")

        abs_script = str(Path(script_path).resolve())
        abs_output = str(Path(output_dir).resolve())
        abs_data = (
            str(Path(data_dir).resolve())
            if Path(data_dir).exists()
            else None
        )

        if not os.path.isfile(abs_script):
            return {
                "stdout": "",
                "stderr": f"Script not found: {abs_script}",
                "exit_code": -1,
            }

        os.makedirs(abs_output, exist_ok=True)

        docker_cmd = [
            "docker", "run",
            "--rm",

            # Security
            "--user", "1000:1000",
            "--memory", self.memory_limit,
            "--cpus", "1.0",
            "--pids-limit", "100",
            "--read-only",
            "--tmpfs", "/tmp:size=100m",
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
        ]

        # Input data (read-only)
        if abs_data and os.path.isdir(abs_data):
            docker_cmd.extend([
                "--mount",
                f"type=bind,source={abs_data},target=/input/data,readonly"
            ])

        # Output directory (read-write)
        docker_cmd.extend([
            "--mount",
            f"type=bind,source={abs_output},target=/output"
        ])

        # Script (read-only)
        docker_cmd.extend([
            "--mount",
            f"type=bind,source={abs_script},target=/input/temp_script.py,readonly"
        ])

        if not self.network:
            docker_cmd.extend(["--network", "none"])

        docker_cmd.extend([
            self.image,
            "python",
            "-u",
            "/input/temp_script.py"
        ])

        print("\n[SANDBOX] Docker command:")
        print(" ".join(map(str, docker_cmd)))
        print()

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            print("[SANDBOX] STDOUT:")
            print(result.stdout)

            print("[SANDBOX] STDERR:")
            print(result.stderr)

            return {
                "stdout": result.stdout[-10000:],
                "stderr": result.stderr[-5000:],
                "exit_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout}s",
                "exit_code": -1,
            }

