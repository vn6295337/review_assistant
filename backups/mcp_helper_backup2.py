#!/usr/bin/env python3
"""
MCP (Master Context Prompt) Helper

This script helps assemble a master context prompt from multiple summary files.
It's designed to consolidate information from chunked file summaries into a
structured prompt for efficient LLM interaction.
"""

import os
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

def load_template(template_path):
    """
    Load a template file and return its content.
    
    Args:
        template_path (str): Path to the template file
        
    Returns:
        str: Content of the template file or None if error
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠ Error loading template: {str(e)}")
        return None

def load_summaries(summaries_dir):
    """
    Load all summary files from the specified directory.
    
    Args:
        summaries_dir (str): Directory containing summary files
        
    Returns:
        list: List of loaded summary data or empty list if error
    """
    summaries = []
    try:
        if not os.path.exists(summaries_dir):
            print(f"⚠ Summaries directory does not exist: {summaries_dir}")
            return []
            
        for filename in os.listdir(summaries_dir):
            if filename.endswith('.json') and filename.startswith('summary_'):
                filepath = os.path.join(summaries_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                        # Make sure the summary is a string, not a nested JSON object
                        if isinstance(summary_data.get('summary'), str):
                            summaries.append(summary_data)
                        else:
                            print(f"⚠ Warning: Summary in {filename} is not a string")
                except Exception as e:
                    print(f"⚠ Error loading summary file {filename}: {str(e)}")
        
        return summaries
        
    except Exception as e:
        print(f"⚠ Error loading summaries: {str(e)}")
        return []

def format_summary_content(summaries):
    """
    Format the summaries into a well-structured text.
    
    Args:
        summaries (list): List of summary data objects
        
    Returns:
        str: Formatted summary content
    """
    if not summaries:
        return "No summaries available."
    
    formatted_content = "## File Summaries\n\n"
    
    # Sort summaries by filename/chunk ID if possible
    try:
        # Extract chunk IDs from source_file paths
        for summary in summaries:
            source_file = summary.get('source_file', '')
            chunk_id = source_file.split('_')[-1].split('.')[0]
            summary['chunk_id'] = int(chunk_id) if chunk_id.isdigit() else 999
        
        # Sort by chunk ID
        summaries.sort(key=lambda x: x.get('chunk_id', 999))
    except:
        # If sorting fails, continue with unsorted summaries
        pass
    
    # Add each summary to the content
    for i, summary in enumerate(summaries):
        summary_text = summary.get('summary', 'No content available')
        formatted_content += f"### Summary {i+1}\n{summary_text}\n\n"
    
    return formatted_content

def create_master_prompt(template_content, summaries, title=None):
    """
    Create a master prompt by filling in the template with summary content.
    
    Args:
        template_content (str): Template string with placeholders
        summaries (list): List of summary data
        title (str, optional): Title for the prompt
        
    Returns:
        str: Filled-in template as the master prompt
    """
    # Generate a default title if none provided
    if not title:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"Chat Review {timestamp}"
    
    # Format the summaries content
    summary_content = format_summary_content(summaries)
    
    # Replace template variables
    prompt = template_content.replace("{summary}", summary_content)
    prompt = prompt.replace("{title}", title)
    
    return prompt

def save_prompt(prompt_content, output_dir):
    """
    Save the generated prompt to a file.
    
    Args:
        prompt_content (str): The prompt content to save
        output_dir (str): Directory to save the prompt file
        
    Returns:
        str: Path to the saved file or None if error
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_prompt_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
            
        return filepath
    except Exception as e:
        print(f"⚠ Error saving prompt: {str(e)}")
        return None

def main():
    """Main function to parse arguments and run the MCP helper."""
    parser = argparse.ArgumentParser(description='Create a master context prompt from summary files')
    parser.add_argument('--template', '-t', type=str, required=True,
                        help='Path to the template file')
    parser.add_argument('--summaries-dir', '-s', type=str, required=True,
                        help='Directory containing summary files')
    parser.add_argument('--output-dir', '-o', type=str, required=True,
                        help='Directory to save the generated prompt')
    parser.add_argument('--title', type=str, 
                        help='Title for the prompt (optional)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Load template
    template_content = load_template(args.template)
    if not template_content:
        sys.exit(1)
    
    # Load summaries
    summaries = load_summaries(args.summaries_dir)
    if args.verbose:
        print(f"Loaded {len(summaries)} summary files")
    
    # Create master prompt
    prompt = create_master_prompt(template_content, summaries, args.title)
    
    # Save prompt
    output_file = save_prompt(prompt, args.output_dir)
    if output_file:
        print(f"✓ Master prompt saved to: {output_file}")
        # Display the file if verbose is enabled
        if args.verbose:
            print("\n--- Prompt Content Preview ---")
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            print("--- End Preview ---\n")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
