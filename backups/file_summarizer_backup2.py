#!/usr/bin/env python3
"""
File Summarizer Script

This script processes chunked JSON files and extracts their content for summarization.
It's part of a local RAG workflow to handle large content files efficiently.
"""

import os
import json
import sys
import argparse
from pathlib import Path

def summarize_chunk(input_file, output_dir):
    """
    Extract content from a JSON chunk file and save as a summary.
    
    Args:
        input_file (str): Path to the input JSON chunk file
        output_dir (str): Directory to save the summary output
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract base filename for the output
        base_name = os.path.basename(input_file)
        output_file = os.path.join(output_dir, f"summary_{base_name}")
        
        # Read and parse the JSON chunk
        with open(input_file, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
        
        # Extract the actual content text (not the whole JSON structure)
        if 'content' in chunk_data:
            content = chunk_data['content']
            chunk_id = chunk_data.get('chunk_id', 'unknown')
            source_file = chunk_data.get('file', 'unknown')
            
            # Create a plain text summary that includes key metadata and the content
            summary = f"Chunk {chunk_id} from {source_file}\n\n{content}"
            
            # Save the summary with proper metadata
            summary_data = {
                "source_file": input_file,
                "summary": summary
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2)
            
            print(f"✓ Summary created: {output_file}")
            return True
        else:
            print(f"⚠ Error: 'content' field missing in {input_file}")
            return False
            
    except Exception as e:
        print(f"⚠ Error processing {input_file}: {str(e)}")
        return False

def process_directory(input_dir, output_dir, verbose=False):
    """
    Process all JSON files in a directory.
    
    Args:
        input_dir (str): Directory containing JSON chunk files
        output_dir (str): Directory to save summary files
        verbose (bool): Whether to print verbose output
    
    Returns:
        int: Number of successfully processed files
    """
    if verbose:
        print(f"Processing directory: {input_dir}")
        print(f"Output directory: {output_dir}")
    
    # Ensure directories exist
    if not os.path.isdir(input_dir):
        print(f"⚠ Input directory does not exist: {input_dir}")
        return 0
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all JSON files
    success_count = 0
    file_count = 0
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            file_count += 1
            input_file = os.path.join(input_dir, filename)
            
            if summarize_chunk(input_file, output_dir):
                success_count += 1
                
    if verbose:
        print(f"\nSummary Generation Complete")
        print(f"Processed {file_count} files")
        print(f"Successfully summarized {success_count} files")
    
    return success_count

def main():
    """Main function to parse arguments and run the summarizer."""
    parser = argparse.ArgumentParser(description='Generate summaries from JSON chunk files')
    parser.add_argument('--input-dir', '-i', type=str, required=True,
                        help='Directory containing chunked JSON files')
    parser.add_argument('--output-dir', '-o', type=str, required=True,
                        help='Directory to save summary outputs')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Process the directory
    process_directory(args.input_dir, args.output_dir, args.verbose)

if __name__ == "__main__":
    main()
