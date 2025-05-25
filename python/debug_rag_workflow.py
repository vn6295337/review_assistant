#!/usr/bin/env python3
"""
Debug RAG Workflow Script

This script checks your RAG workflow setup and diagnoses common issues.
"""

import os
import json
import sys
import glob
from pathlib import Path

# Configuration
ROOT_DIR = "/mnt/chromeos/removable/USB Drive/review_assistant"
PYTHON_DIR = os.path.join(ROOT_DIR, "python")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
SUMMARIES_DIR = os.path.join(ROOT_DIR, "outputs/summaries")
CHUNKS_RAW_DIR = os.path.join(ROOT_DIR, "chunks")
CHUNKS_OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs/chunks")
PROMPTS_DIR = os.path.join(ROOT_DIR, "outputs/prompts")

def print_section_header(title):
    """Print a section header."""
    print(f"\n# ================================================================================")
    print(f"{title}\n")

def check_directory(dir_path, required=True):
    """Check if a directory exists and print the result."""
    if os.path.isdir(dir_path):
        print(f"✓ Directory exists: {dir_path}")
        return True
    else:
        status = "❌" if required else "⚠"
        print(f"{status} Directory does not exist: {dir_path}")
        return False

def check_file(file_path, required=True):
    """Check if a file exists and print the result."""
    if os.path.isfile(file_path):
        print(f"✓ File exists: {file_path}")
        return True
    else:
        status = "❌" if required else "⚠"
        print(f"{status} File does not exist: {file_path}")
        return False

def check_json_file(file_path):
    """Check if a file contains valid JSON and print contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✓ Valid JSON found in {file_path}")
            print(f"ℹ {os.path.basename(file_path)} content keys: {', '.join(data.keys())}")
            
            # Print each key-value pair (truncated if large)
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 500:
                    value_preview = value[:500] + "..."
                else:
                    value_preview = value
                print(f"ℹ   {key}: {value_preview}")
            
            return data
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading {file_path}: {str(e)}")
        return None

def list_directory_files(dir_path, pattern="*", max_display=5):
    """List files in a directory matching a pattern."""
    files = glob.glob(os.path.join(dir_path, pattern))
    
    if files:
        print(f"✓ Found {len(files)} files in {dir_path}")
        for i, file in enumerate(sorted(files)):
            if i < max_display:
                print(f"ℹ   - {os.path.basename(file)}")
            elif i == max_display:
                remaining = len(files) - max_display
                print(f"ℹ   ... and {remaining} more")
        return files
    else:
        print(f"⚠ No files matching {pattern} found in {dir_path}")
        return []

def check_template_variables(template_path):
    """Check template file for variables and substitution."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find template variables using regex pattern {variable_name}
        import re
        variables = re.findall(r'\{([a-zA-Z0-9_]+)\}', content)
        unique_vars = list(set(variables))
        
        if unique_vars:
            print(f"✓ Found {len(unique_vars)} template variables: {', '.join(unique_vars)}")
        else:
            print("⚠ No template variables found in template file")
            
        return unique_vars
    except Exception as e:
        print(f"❌ Error analyzing template file {template_path}: {str(e)}")
        return []

def check_prompt_content(prompt_path):
    """Check content of a generated prompt file."""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"ℹ Prompt content (first 500 chars):\n")
        print(content[:500])
        
        # Check for unreplaced template variables
        import re
        template_vars = re.findall(r'\{([a-zA-Z0-9_]+)\}', content)
        if template_vars:
            print(f"\n⚠ Unreplaced template variables found: {template_vars}")
            
        # Check for raw JSON content that should have been extracted
        json_fragments = re.findall(r'"source_file":|"summary":', content)
        if json_fragments:
            print(f"\n⚠ JSON fragments found in prompt content. The summary extraction may not be working correctly.")
            
        return content
    except Exception as e:
        print(f"❌ Error reading prompt file {prompt_path}: {str(e)}")
        return None

def main():
    """Main function to check the RAG workflow setup."""
    # Check environment setup
    print_section_header("Checking Environment Setup")
    check_directory(ROOT_DIR)
    check_directory(PYTHON_DIR)
    check_directory(TEMPLATES_DIR)
    check_directory(SUMMARIES_DIR)
    check_directory(CHUNKS_RAW_DIR)
    check_directory(CHUNKS_OUTPUT_DIR)
    check_directory(PROMPTS_DIR)
    
    # Check Python scripts
    print_section_header("Checking Python Scripts")
    check_file(os.path.join(PYTHON_DIR, "file_chunker.py"))
    check_file(os.path.join(PYTHON_DIR, "file_summarizer.py"))
    check_file(os.path.join(PYTHON_DIR, "mcp_helper.py"))
    
    # Check template file
    print_section_header("Checking Template File")
    template_file = os.path.join(TEMPLATES_DIR, "summary_prompt_template.md")
    if check_file(template_file):
        check_template_variables(template_file)
    
    # Check chunk files
    print_section_header("Checking Chunk Files")
    if check_directory(CHUNKS_RAW_DIR):
        chunk_files = list_directory_files(CHUNKS_RAW_DIR, "*.json")
        if chunk_files:
            print(f"ℹ Examining first chunk file:")
            check_json_file(chunk_files[0])
    
    # Check summary files
    print_section_header("Checking Summary Files")
    if check_directory(SUMMARIES_DIR):
        summary_files = list_directory_files(SUMMARIES_DIR, "summary_*.json")
        if summary_files:
            print(f"ℹ Examining first summary file:")
            summary_data = check_json_file(summary_files[0])
            
            # Check if summary is plain text or still JSON
            if summary_data and "summary" in summary_data:
                summary_content = summary_data["summary"]
                if summary_content.startswith("{") and ("id" in summary_content or "content" in summary_content):
                    print("⚠ WARNING: Summary appears to be a JSON string, not a plain text summary.")
                    print("⚠    This indicates the file_summarizer.py script is not properly extracting content.")
    
    # Check prompt output
    print_section_header("Checking Prompt Output")
    if check_directory(PROMPTS_DIR):
        prompt_files = list_directory_files(PROMPTS_DIR, "summary_prompt_*.txt")
        if prompt_files:
            print(f"ℹ Examining first prompt file:")
            check_prompt_content(prompt_files[0])
    
    # Provide a summary and next steps
    print_section_header("Debug Summary")
    print("ℹ ")
    print("ℹ Next steps recommendations:")
    print("ℹ ")
    print("ℹ 1. Make sure file_summarizer.py properly extracts plain text content from chunks")
    print("ℹ 2. Ensure mcp_helper.py correctly renders templates with the extracted content")
    print("ℹ 3. Check that summary_prompt_template.md has the correct variable placeholders")
    print("ℹ 4. Run the full_rag_workflow.sh script with verbose logs to trace any issues")

if __name__ == "__main__":
    main()
