#!/usr/bin/env python3
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    try:
        print(f"Running {description}...")
        subprocess.run(cmd, check=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found. Make sure you're in the backend directory and have poetry installed.")
        return False

def format_folder(path: Path, skip_mypy: bool = False, check_only: bool = False) -> bool:
    """Format a folder with ruff and optionally run mypy."""
    if not path.exists():
        print(f"Error: {path} does not exist")
        return False
    
    if not path.is_dir():
        print(f"Error: {path} is not a directory")
        return False
    
    print(f"Formatting folder: {path}")
    
    # Run ruff format
    ruff_cmd = ["poetry", "run", "ruff", "format"]
    if check_only:
        ruff_cmd.append("--check")
    ruff_cmd.append(str(path))
    
    if not run_command(ruff_cmd, "Ruff formatting"):
        return False
    
    # Run mypy type check (unless skipped)
    if not skip_mypy:
        mypy_cmd = ["poetry", "run", "mypy", str(path)]
        if not run_command(mypy_cmd, "MyPy type checking"):
            return False
    
    return True

def format_file(path: Path, skip_mypy: bool = False, check_only: bool = False) -> bool:
    """Format a single file with ruff and optionally run mypy."""
    if not path.exists():
        print(f"Error: {path} does not exist")
        return False
    
    if not path.is_file():
        print(f"Error: {path} is not a file")
        return False
    
    print(f"Formatting file: {path}")
    
    # Run ruff format
    ruff_cmd = ["poetry", "run", "ruff", "format"]
    if check_only:
        ruff_cmd.append("--check")
    ruff_cmd.append(str(path))
    
    if not run_command(ruff_cmd, "Ruff formatting"):
        return False
    
    # Run mypy type check (unless skipped)
    if not skip_mypy:
        mypy_cmd = ["poetry", "run", "mypy", str(path)]
        if not run_command(mypy_cmd, "MyPy type checking"):
            return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Format Python files and folders")
    parser.add_argument("path", help="File or directory to format")
    parser.add_argument("--skip-mypy", action="store_true", help="Skip MyPy type checking")
    parser.add_argument("--check-only", action="store_true", help="Check formatting without making changes")
    parser.add_argument("--folder", action="store_true", help="Force treating path as a folder")
    
    args = parser.parse_args()
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: {path} does not exist")
        sys.exit(1)
    
    success = False
    
    if args.folder or path.is_dir():
        success = format_folder(path, args.skip_mypy, args.check_only)
    else:
        success = format_file(path, args.skip_mypy, args.check_only)
    
    if success:
        print("🎉 All done!")
    else:
        print("❌ Formatting failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 