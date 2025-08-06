"""Scanner for development environment tools."""

import subprocess
from typing import Any, Dict, List


class DevEnvScanner:
    """Scans for installed development tools and toolchains."""

    # Common development tools to check for
    DEV_TOOLS = [
        {"name": "git", "command": "git --version", "description": "Git version control"},
        {"name": "python", "command": "python3 --version", "description": "Python interpreter"},
        {"name": "node", "command": "node --version", "description": "Node.js runtime"},
        {"name": "npm", "command": "npm --version", "description": "Node Package Manager"},
        {"name": "yarn", "command": "yarn --version", "description": "Yarn package manager"},
        {"name": "go", "command": "go version", "description": "Go programming language"},
        {"name": "rust", "command": "rustc --version", "description": "Rust programming language"},
        {"name": "java", "command": "java --version", "description": "Java runtime"},
        {"name": "docker", "command": "docker --version", "description": "Docker containerization"},
        {"name": "kubectl", "command": "kubectl version --client", "description": "Kubernetes CLI"},
        {"name": "terraform", "command": "terraform version", "description": "Terraform infrastructure tool"},
        {"name": "aws", "command": "aws --version", "description": "AWS CLI"},
        {"name": "gcloud", "command": "gcloud version", "description": "Google Cloud CLI"},
        {"name": "az", "command": "az version", "description": "Azure CLI"},
    ]

    def scan(self) -> Dict[str, Any]:
        """Scan for installed development tools."""
        installed_tools = []
        missing_tools = []

        for tool in self.DEV_TOOLS:
            tool_info = self._check_tool_installed(tool)
            if tool_info["installed"]:
                installed_tools.append(tool_info)
            else:
                missing_tools.append(tool_info)

        return {
            "installed_tools": installed_tools,
            "missing_tools": missing_tools,
            "installed_count": len(installed_tools),
            "missing_count": len(missing_tools),
            "total_count": len(self.DEV_TOOLS),
        }

    def _check_tool_installed(self, tool: Dict[str, str]) -> Dict[str, Any]:
        """Check if a development tool is installed."""
        try:
            result = subprocess.run(
                tool["command"].split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Extract version info from output
                version_output = result.stdout.strip() or result.stderr.strip()
                return {
                    "name": tool["name"],
                    "description": tool["description"],
                    "installed": True,
                    "version_info": version_output.split('\n')[0]  # First line only
                }
            else:
                return {
                    "name": tool["name"],
                    "description": tool["description"],
                    "installed": False,
                    "version_info": None
                }
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "name": tool["name"],
                "description": tool["description"],
                "installed": False,
                "version_info": None
            }
