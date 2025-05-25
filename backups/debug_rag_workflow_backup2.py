#!/usr/bin/env python3
"""
Debug RAG Workflow Script

This script inspects the RAG workflow components and validates
the setup, identifying issues and providing recommendations.
"""

import os
import json
import sys
import glob
from datetime import datetime

# Set up color formatting for terminal output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(message):
    """Print a section header with consistent formatting."""
    print(f"\n# {'=' * 80}")
    print(f"{message}")
    print()

def print_success(message):
    """Print a success message."""
    print(f"✓ {message}")

def print_warning(message):
    """Print a warning message."""
    print(f"⚠ {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ {message}")

def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")

def check_directory(directory, description=None):
    """Check if a directory exists and print the result."""
    if os.path.isdir(directory):
        print_success(f"{description or 'Directory'} exists: {directory}")
        return True
    else:
        print_error(f"{description or 'Directory'} does not exist: {directory}")
        return False

def check_file(filepath, description=None):
    """Check if a file exists and print the result."""
    if os.path.isfile(filepath):
        print_success(f"{description or 'File'} exists: {filepath}")
        return True
    else:
        print_error(f"{description or 'File'} does not exist: {filepath}")
        return False

def examine_json_file(filepath):
    """Examine the contents of a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print_success(f"Valid JSON found in {filepath}")
            
            # Print the keys
            keys = ", ".join(data.keys())
            print_info(f"{os.path.basename(filepath)} content keys: {keys}")
            
            # Print some values (first 200 chars for strings)
            for key, value in data.items():
                if isinstance(value, str):
                    # Truncate long strings
                    display_value = value[:200] + "..." if len(value) > 200 else value
                    print_info(f"  {key}: {display_value}")
                else:
                    print_info(f"  {key}: {value}")
            
            return data
    except json.JSONDecodeError:
        print_error(f"Invalid JSON format in {filepath}")
        return None
    except Exception as e:
        print_error(f"Error examining {filepath}: {str(e)}")
        return None

def check_template_file(filepath):
    """Check and analyze a template file."""
    if not check_file(filepath, "Template file"):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find template variables in the format {variable_name}
        import re
        variables = re.findall(r'\{([^}]+)\}', content)
        variables = list(set(variables))  # Remove duplicates
        
        print_success(f"Found {len(variables)} template variables: {', '.join(variables)}")
        return True
    except Exception as e:
        print_error(f"Error analyzing template: {str(e)}")
        return False

def check_chunks_directory(directory):
    """Check the chunks directory and examine a sample chunk."""
    if not check_directory(directory):
        return
    
    # List chunk files
    chunk_files = glob.glob(os.path.join(directory, "*.json"))
    
    if not chunk_files:
        print_warning(f"No chunk files found in {directory}")
        return
    
    print_success(f"Found {len(chunk_files)} files in {directory}")
    
    # Display a few filenames
    max_display = 5
    for i in range(min(max_display, len(chunk_files))):
        print_info(f"  - {os.path.basename(chunk_files[i])}")
    
    if len(chunk_files) > max_display:
        print_info(f"  ... and {len(chunk_files) - max_display} more")
    
    # Examine the first chunk file
    print_info(f"Examining first chunk file:")
    examine_json_file(chunk_files[0])

def check_summaries_directory(directory):
    """Check the summaries directory and examine a sample summary."""
    if not check_directory(directory):
        return
    
    # List summary files
    summary_files = glob.glob(os.path.join(directory, "*.json"))
    
    if not summary_files:
        print_warning(f"No summary files found in {directory}")
        return
    
    print_success(f"Found {len(summary_files)} files in {directory}")
    
    # Display a few filenames
    max_display = 5
    for i in range(min(max_display, len(summary_files))):
        print_info(f"  - {os.path.basename(summary_files[i])}")
    
    if len(summary_files) > max_display:
        print_info(f"  ... and {len(summary_files) - max_display} more")
    
    # Examine the first summary file
    print_info(f"Examining first summary file:")
    summary_data = examine_json_file(summary_files[0])
    
    # Check if the summary looks like JSON instead of plain text
    if summary_data and 'summary' in summary_data:
        summary = summary_data['summary']
        if summary.strip().startswith('{') and '"' in summary:
            print_warning("WARNING: Summary appears to be a JSON string, not a plain text summary.")
            print_warning("   This indicates the file_summarizer.py script is not properly extracting content.")

def check_prompts_directory(directory):
    """Check the prompts directory and examine a sample prompt."""
    if not check_directory(directory):
        return
    
    # List prompt files
    prompt_files = glob.glob(os.path.join(directory, "*.txt"))
    
    if not prompt_files:
        print_warning(f"No prompt files found in {directory}")
        return
    
    print_success(f"Found {len(prompt_files)} files in {directory}")
    
    # Display a few filenames
    max_display = 5
    for i in range(min(max_display, len(prompt_files))):
        print_info(f"  - {os.path.basename(prompt_files[i])}")
    
    # Display the content of the most recent prompt file
    newest_prompt = max(prompt_files, key=os.path.getmtime)
    print_info(f"Examining first prompt file:")
    
    try:
        with open(newest_prompt, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print_info(f"Prompt content (first 500 chars):\n")
        print(content[:500] + "..." if len(content) > 500 else content)
        
        # Check if all template variables were replaced
        import re
        variables = re.findall(r'\{([^}]+)\}', content)
        
        if variables:
            print_warning(f"Unreplaced template variables found: {', '.join(variables)}")
        else:
            print_success("All template variables were properly replaced")
            
    except Exception as e:
        print_error(f"Error examining prompt file: {str(e)}")

def main():
    """Main function to check RAG workflow components."""
    # Define directories
    root_dir = os.getcwd()
    python_dir = os.path.join(root_dir, "python")
    templates_dir = os.path.join(root_dir, "templates")
    summaries_dir = os.path.join(root_dir, "outputs", "summaries")
    chunks_raw_dir = os.path.join(root_dir, "chunks")
    chunks_output_dir = os.path.join(root_dir, "outputs", "chunks")
    prompts_dir = os.path.join(root_dir, "outputs", "prompts")
    
    # Check environment setup
    print_header("Checking Environment Setup")
    check_directory(root_dir, "Root directory")
    check_directory(python_dir, "Python scripts directory")
    check_directory(templates_dir, "Templates directory")
    check_directory(summaries_dir, "Summaries directory")
    check_directory(chunks_raw_dir, "Chunks raw directory")
    check_directory(chunks_output_dir, "Chunks output directory")
    check_directory(prompts_dir, "Prompts directory")
    
    # Check Python scripts
    print_header("Checking Python Scripts")
    check_file(os.path.join(python_dir, "file_chunker.py"), "File chunker")
    check_file(os.path.join(python_dir, "file_summarizer.py"), "File summarizer")
    check_file(os.path.join(python_dir, "mcp_helper.py"), "MCP helper")
    
    # Check template file
    print_header("Checking Template File")
    template_file = os.path.join(templates_dir, "summary_prompt_template.md")
    check_template_file(template_file)
    
    # Check chunks
    print_header("Checking Chunk Files")
    check_chunks_directory(chunks_raw_dir)
    
    # Check summaries
    print_header("Checking Summary Files")
    check_summaries_directory(summaries_dir)
    
    # Check prompts
    print_header("Checking Prompt Output")
    check_prompts_directory(prompts_dir)
    
    # Summary and recommendations
    print_header("Debug Summary")
    print_info("")
    print_info("Next steps recommendations:")
    print_info("")
    print_info("1. First, check and fix your file_summarizer.py script to properly extract content from JSON chunks")
    print_info("   The summary should contain plain text, not nested JSON fragments")
    print_info("2. Make sure mcp_helper.py correctly processes nested JSON data if needed")
    print_info("3. Run the full_rag_workflow.sh script again after making these fixes")
    print_info("4. For specific script issues, run them individually with verbose logging enabled")

if __name__ == "__main__":
    main()
