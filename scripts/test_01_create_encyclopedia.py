#!/usr/bin/env python3
"""
Test 1: Read wordlist and create encyclopedia without description or images

CLI-based test that creates a basic encyclopedia from a wordlist file.
"""
import subprocess
import sys
from pathlib import Path
from encyclopedia.utils.resources import Resources


def main():
    """Run test 1: Create encyclopedia from wordlist."""
    print("="*60)
    print("Test 1: Create Encyclopedia from Wordlist")
    print("="*60)
    
    # Get version from CLI
    cmd_version = [
        sys.executable, "-m", "encyclopedia.cli.versioned_editor",
        "--version"
    ]
    result = subprocess.run(cmd_version, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Encyclopedia version: {result.stdout.strip()}")
    print()
    
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Input: wordlist from test/ directory
    wordlist_file = Path(project_root, "test", "wordlist_a.txt")
    
    if not wordlist_file.exists():
        print(f"❌ Error: Wordlist file not found: {wordlist_file}")
        return 1
    
    # Output: temp/test/wordlist_a/encyclopedia.html (structured to reflect input)
    output_dir = Resources.get_temp_dir("test", "wordlist_a")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = Path(output_dir, "encyclopedia.html")
    
    print(f"\nInput wordlist: {wordlist_file}")
    print(f"Output encyclopedia: {output_file}")
    
    # Run CLI command
    cmd = [
        sys.executable, "-m", "encyclopedia.cli.versioned_editor",
        "create",
        "--wordlist", str(wordlist_file),
        "--output", str(output_file),
        "--title", "Test Encyclopedia"
    ]
    
    print(f"\nRunning: {' '.join(cmd)}")
    print("-"*60)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        print("-"*60)
        print(f"✅ Test 1 passed: Encyclopedia created successfully")
        print(f"   Output: {output_file}")
        
        # Verify output exists
        if output_file.exists():
            content = output_file.read_text()
            entry_count = content.count('role="ami_entry"')
            print(f"   Entries created: {entry_count}")
        else:
            print(f"   ⚠️  Warning: Output file not found")
        
        return 0
    else:
        print("-"*60)
        print(f"❌ Test 1 failed: Exit code {result.returncode}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
