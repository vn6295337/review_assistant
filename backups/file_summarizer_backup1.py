#!/usr/bin/env python3
"""
File summarizer that processes text chunks and generates summaries.
Can process either individual files or directories containing chunk files.
"""

import argparse
import os
import sys
import json
from pathlib import Path

def summarize_content(content):
    """
    Generate a summary of the provided content.
    This is a simple implementation that extracts the first few sentences.
    For better results, consider using an LLM or more sophisticated summarization techniques.
    """
    # Simple summary logic - take first ~200 characters that end with a period
    sentences = content.split('.')
    summary = ''
    for sentence in sentences:
        if len(summary) + len(sentence) < 200:
            summary += sentence + '.'
        else:
            break
    
    return summary.strip()

def process_file(file_path, output_dir):
    """Process a single file and generate a summary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                # Try to parse as JSON first
                chunk_data = json.load(f)
                
                # Extract the actual content to summarize from JSON structure
                if isinstance(chunk_data, dict) and 'content' in chunk_data:
                    content_to_summarize = chunk_data['content']
                else:
                    # If JSON doesn't have expected structure, use as-is
                    content_to_summarize = json.dumps(chunk_data)
            except json.JSONDecodeError:
                # If not JSON, read the file as raw text
                f.seek(0)
                content_to_summarize = f.read()
                
        # Generate summary of the extracted content
        summary = summarize_content(content_to_summarize)
        
        # Create output filename based on input filename
        base_filename = os.path.basename(file_path)
        summary_filename = f"summary_{base_filename}"
        summary_path = os.path.join(output_dir, summary_filename)
        
        # Save summary
        with open(summary_path, 'w', encoding='utf-8') as f:
            summary_data = {
                'source_file': str(file_path),
                'summary': summary  # Store the actual summary text, not a JSON fragment
            }
            json.dump(summary_data, f, indent=2)
            
        print(f"Created summary for {file_path} at {summary_path}")
        return True
        
    except Exception as e:
        print(f"Failed to create summary for {file_path}: {str(e)}")
        return False

def process_directory(dir_path, output_dir):
    """Process all files in a directory and generate summaries."""
    success_count = 0
    failure_count = 0
    
    # Ensure the directory exists
    if not os.path.isdir(dir_path):
        print(f"Error: {dir_path} is not a directory")
        return False
    
    # Get all files in the directory
    files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    
    if not files:
        print(f"No files found in {dir_path}")
        return False
    
    print(f"Found {len(files)} files to process in {dir_path}")
    
    # Process each file
    for i, filename in enumerate(files, 1):
        file_path = os.path.join(dir_path, filename)
        print(f"Processing {i}/{len(files)}: {filename}...")
        if process_file(file_path, output_dir):
            success_count += 1
        else:
            failure_count += 1
    
    print(f"Summary processing complete. Successful: {success_count}, Failed: {failure_count}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Generate summaries from text files or chunks')
    parser.add_argument('source', help='Source file or directory containing text chunks')
    parser.add_argument('--output', help='Output directory for summaries', default='summaries')
    
    args = parser.parse_args()
    
    source_path = args.source
    output_dir = args.output
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if source is a file or directory
    if os.path.isfile(source_path):
        print(f"Processing single file: {source_path}")
        process_file(source_path, output_dir)
    elif os.path.isdir(source_path):
        print(f"Processing directory: {source_path}")
        process_directory(source_path, output_dir)
    else:
        print(f"Error: {source_path} is neither a file nor a directory")
        sys.exit(1)
    
    print(f"Summaries saved to {output_dir}")

if __name__ == "__main__":
    main()
