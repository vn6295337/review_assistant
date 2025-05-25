#!/usr/bin/env python3
"""
Debug script for the RAG workflow
Systematically checks each component and reports any issues
"""

import os
import sys
import json
import glob
from pathlib import Path
import datetime

def check_directory(dir_path, name):
    """Check if a directory exists"""
    exists = os.path.isdir(dir_path)
    if exists:
        print(f"✓ {name} exists: {dir_path}")
    else:
        print(f"✗ {name} NOT FOUND: {dir_path}")
    return exists

def check_file(file_path, name):
    """Check if a file exists"""
    exists = os.path.isfile(file_path)
    if exists:
        print(f"✓ {name} exists: {file_path}")
    else:
        print(f"✗ {name} NOT FOUND: {file_path}")
    return exists

def examine_json_file(file_path, display_limit=300):
    """Examine a JSON file for validity and content structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            data = json.loads(content)
            print(f"✓ Valid JSON found in {file_path}")
            
            # Print some details about the data structure
            print(f"ℹ {file_path.name} content keys:", ', '.join(data.keys()) if isinstance(data, dict) else "Not a dictionary")
            
            # Extract a sample of the content
            if isinstance(data, dict):
                for key, value in data.items():
                    value_str = str(value)
                    if len(value_str) > display_limit:
                        value_str = value_str[:display_limit] + "..."
                    print(f"ℹ   {key}: {value_str}")
            return True, data
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in {file_path}")
        return False, None
    except Exception as e:
        print(f"✗ Error examining {file_path}: {e}")
        return False, None

def check_template_variables(template_path):
    """Check template file for variables"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all template variables {{var}}
        import re
        variables = re.findall(r'\{\{([^}]+)\}\}', content)
        unique_vars = set(variables)
        
        print(f"✓ Found {len(unique_vars)} template variables: {', '.join(unique_vars)}")
        return unique_vars
    except Exception as e:
        print(f"✗ Error checking template variables in {template_path}: {e}")
        return set()

def check_prompt_variables(prompt_path, expected_vars):
    """Check if all template variables were replaced in the prompt"""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Display a sample of the prompt content
            print(f"ℹ Prompt content (first 500 chars):\n\n{content[:500]}")
            
        # Check if any template variables remain unreplaced
        import re
        remaining_vars = re.findall(r'\{\{([^}]+)\}\}', content)
        
        if remaining_vars:
            print(f"✗ Found {len(remaining_vars)} unreplaced variables: {', '.join(remaining_vars)}")
            return False
        else:
            print(f"✓ All template variables were properly replaced")
            return True
    except Exception as e:
        print(f"✗ Error checking prompt variables in {prompt_path}: {e}")
        return False

def main():
    # Root directory
    root_dir = "/mnt/chromeos/removable/USB Drive/review_assistant"
    
    print("\n# " + "=" * 80)
    print("Checking Environment Setup\n")
    
    # Check directory structure
    dirs_to_check = {
        "Root directory": root_dir,
        "Python scripts directory": os.path.join(root_dir, "python"),
        "Templates directory": os.path.join(root_dir, "templates"),
        "Summaries directory": os.path.join(root_dir, "outputs/summaries"),
        "Chunks raw directory": os.path.join(root_dir, "chunks"),
        "Chunks output directory": os.path.join(root_dir, "outputs/chunks"),
        "Prompts directory": os.path.join(root_dir, "outputs/prompts"),
    }
    
    for name, dir_path in dirs_to_check.items():
        check_directory(dir_path, name)
    
    print("\n# " + "=" * 80)
    print("Checking Python Scripts\n")
    
    # Check essential Python scripts
    py_dir = os.path.join(root_dir, "python")
    scripts_to_check = {
        "File chunker": os.path.join(py_dir, "file_chunker.py"),
        "File summarizer": os.path.join(py_dir, "file_summarizer.py"),
        "MCP helper": os.path.join(py_dir, "mcp_helper.py"),
    }
    
    for name, script_path in scripts_to_check.items():
        check_file(script_path, name)
    
    print("\n# " + "=" * 80)
    print("Checking Template File\n")
    
    # Check template file
    template_path = os.path.join(root_dir, "templates/summary_prompt_template.md")
    if check_file(template_path, "Template file"):
        expected_vars = check_template_variables(template_path)

    print("\n# " + "=" * 80)
    print("Checking Chunk Files\n")
    
    # Check chunk files
    chunks_dir = os.path.join(root_dir, "chunks")
    chunk_files = glob.glob(os.path.join(chunks_dir, "*.json"))
    
    if chunk_files:
        print(f"✓ Found {len(chunk_files)} files in {chunks_dir}")
        # List first few files
        max_files_to_show = 5
        for i, chunk_file in enumerate(chunk_files[:max_files_to_show]):
            print(f"ℹ   - {os.path.basename(chunk_file)}")
        if len(chunk_files) > max_files_to_show:
            print(f"ℹ   ... and {len(chunk_files) - max_files_to_show} more")
        
        # Examine first chunk file in detail
        first_chunk = chunk_files[0]
        print(f"ℹ Examining first chunk file:")
        valid, chunk_data = examine_json_file(Path(first_chunk))
    else:
        print(f"✗ No chunk files found in {chunks_dir}")
    
    print("\n# " + "=" * 80)
    print("Checking Summary Files\n")
    
    # Check summary files
    summary_dir = os.path.join(root_dir, "outputs/summaries")
    summary_files = glob.glob(os.path.join(summary_dir, "summary_*.json"))
    
    if summary_files:
        print(f"✓ Found {len(summary_files)} files in {summary_dir}")
        # List first few files
        max_files_to_show = 5
        for i, summary_file in enumerate(summary_files[:max_files_to_show]):
            print(f"ℹ   - {os.path.basename(summary_file)}")
        if len(summary_files) > max_files_to_show:
            print(f"ℹ   ... and {len(summary_files) - max_files_to_show} more")
        
        # Examine first summary file in detail
        first_summary = summary_files[0]
        print(f"ℹ Examining first summary file:")
        valid, summary_data = examine_json_file(Path(first_summary))
        
        # IMPORTANT: Check if summary is properly structured
        if valid and isinstance(summary_data, dict) and 'summary' in summary_data:
            summary_value = summary_data['summary']
            if isinstance(summary_value, str):
                if summary_value.startswith("{") and "\\n" in summary_value:
                    print("⚠ WARNING: Summary appears to be a JSON string, not a plain text summary.")
                    print("   This indicates the file_summarizer.py script is not properly extracting content.")
            elif not isinstance(summary_value, str):
                print("⚠ WARNING: Summary value is not a string. Check file_summarizer.py logic.")
    else:
        print(f"✗ No summary files found in {summary_dir}")
    
    print("\n# " + "=" * 80)
    print("Checking Prompt Output\n")
    
    # Check prompt output
    prompts_dir = os.path.join(root_dir, "outputs/prompts")
    prompt_files = glob.glob(os.path.join(prompts_dir, "*.txt"))
    
    if prompt_files:
        print(f"✓ Found {len(prompt_files)} files in {prompts_dir}")
        # List files
        for prompt_file in prompt_files:
            print(f"ℹ   - {os.path.basename(prompt_file)}")
        
        # Examine last modified prompt file
        latest_prompt = max(prompt_files, key=os.path.getmtime)
        print(f"ℹ Examining first prompt file:")
        if check_template_variables and expected_vars:
            check_prompt_variables(latest_prompt, expected_vars)
    else:
        print(f"✗ No prompt files found in {prompts_dir}")
    
    print("\n# " + "=" * 80)
    print("Debug Summary\n")
    
    print("ℹ")
    print("Next steps recommendations:")
    print("ℹ")
    print("1. First, check and fix your file_summarizer.py script to properly extract content from JSON chunks")
    print("   The summary should contain plain text, not nested JSON fragments")
    print("2. Make sure mcp_helper.py correctly processes nested JSON data if needed")
    print("3. Run the full_rag_workflow.sh script again after making these fixes")
    print("4. For specific script issues, run them individually with verbose logging enabled.")

if __name__ == "__main__":
    main()
