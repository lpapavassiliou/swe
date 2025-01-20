import subprocess
import sys
from pathlib import Path

def _run_command(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        sys.exit(e.returncode)

def install_command():
    """Install SWE using pipx"""
    # Clean old builds and install dependencies
    try:
        _run_command(["rm", "-rf", "dist"])
        _run_command(["poetry", "install"])
    except Exception as e:
        print(f"Error during cleanup or dependency installation: {e}")
        return

    # Build the package
    try:
        _run_command(["poetry", "build"])
    except Exception as e:
        print(f"Error building the package: {e}")
        return

    # Install with pipx
    try:
        dist_path = next(Path("dist").glob("swe-*.whl"))
        _run_command(["pipx", "install", str(dist_path)])
    except Exception as e:
        print(f"Error installing the package: {e}")

def update_command():
    """Update SWE to the latest version"""
    # Clean, install dependencies, and rebuild
    try:
        _run_command(["rm", "-rf", "dist"])
        _run_command(["poetry", "install"])
        _run_command(["poetry", "build"])
    except Exception as e:
        print(f"Error during cleanup, install, or rebuild: {e}")
        return

    # Uninstall if exists
    result = subprocess.run(["pipx", "list"], capture_output=True, text=True)
    if "swe" in result.stdout:
        try:
            _run_command(["pipx", "uninstall", "swe"])
        except Exception as e:
            print(f"Error uninstalling the old version: {e}")
            return

    # Install new version
    try:
        dist_path = next(Path("dist").glob("swe-*.whl"))
        _run_command(["pipx", "install", str(dist_path)])
    except Exception as e:
        print(f"Error installing the new version: {e}")

def uninstall_command():
    """Uninstall SWE completely"""
    # Clean old builds first
    try:
        _run_command(["rm", "-rf", "dist"])
    except Exception as e:
        print(f"Error cleaning dist directory: {e}")
        return
    try:
        _run_command(["pipx", "uninstall", "swe"])
        print("SWE has been uninstalled successfully globally.")
    except Exception as e:
        print(f"Error uninstalling the package: {e}")
