#!/usr/bin/env python3
"""
Process repository changes with Claude API.
This script reads the changed files and sends them to Claude for processing.
"""

import anthropic
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Optional

def read_file_safely(file_path: str) -> Optional[str]:
    """
    Safely read a file, handling binary files gracefully.
    Returns None for binary files, file content for text files.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Binary file - return indicator
        return f"[Binary file: {file_path}]"
    except FileNotFoundError:
        return f"[File not found: {file_path}]"
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def get_changed_files_content(files_str: str) -> dict:
    """
    Parse the changed files string and read their content.
    Returns a dictionary of {filename: content}.
    """
    file_contents = {}
    
    if not files_str.strip():
        return file_contents
    
    for file_path in files_str.strip().split('\n'):
        if file_path:
            content = read_file_safely(file_path)
            if content:
                file_contents[file_path] = content
    
    return file_contents

def process_with_claude(
    files: dict,
    commit_message: str,
    commit_author: str,
    repo: str,
    commit_sha: str
) -> str:
    """
    Send changed files to Claude for processing.
    Customize this function based on your needs.
    """
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Prepare the file contents string
    files_str = ""
    for filename, content in files.items():
        files_str += f"\n\n{'='*60}\nFile: {filename}\n{'='*60}\n{content}"
    
    # Craft your processing prompt here
    prompt = f"""
Repository: {repo}
Commit SHA: {commit_sha}
Author: {commit_author}
Message: {commit_message}

The following files have been changed in this commit:

{files_str}

Please analyze these changes and provide:
1. Summary of what changed
2. Any potential issues or concerns
3. Suggestions for improvement
4. Any patterns or best practices violations you notice
"""
    
    # Call Claude API
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return message.content[0].text

def save_results(results: str, output_file: str = "claude_output.json") -> None:
    """Save the Claude processing results to a JSON file."""
    output_data = {
        "status": "success",
        "analysis": results,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Results saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Process repository changes with Claude API"
    )
    parser.add_argument("--files", required=True, help="Changed files (newline separated)")
    parser.add_argument("--commit-message", required=True, help="Commit message")
    parser.add_argument("--commit-author", required=True, help="Commit author")
    parser.add_argument("--repo", required=True, help="Repository name (owner/repo)")
    parser.add_argument("--commit-sha", required=True, help="Commit SHA")
    
    args = parser.parse_args()
    
    print(f"Processing changes for {args.repo}")
    print(f"Commit: {args.commit_sha}")
    print(f"Author: {args.commit_author}")
    print(f"Message: {args.commit_message}\n")
    
    # Read the changed files
    file_contents = get_changed_files_content(args.files)
    
    if not file_contents:
        print("No files to process.")
        return
    
    print(f"Found {len(file_contents)} changed file(s)")
    for filename in file_contents.keys():
        print(f"  - {filename}")
    
    # Process with Claude
    print("\nSending to Claude for analysis...\n")
    results = process_with_claude(
        files=file_contents,
        commit_message=args.commit_message,
        commit_author=args.commit_author,
        repo=args.repo,
        commit_sha=args.commit_sha
    )
    
    # Print and save results
    print("Claude Analysis:")
    print("="*60)
    print(results)
    print("="*60)
    
    save_results(results)

if __name__ == "__main__":
    main()
