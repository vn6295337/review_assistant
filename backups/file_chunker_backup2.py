#!/usr/bin/env python3
"""
File Chunker Script

This script breaks down large files into manageable chunks for processing.
It's designed to handle files that exceed LLM context windows.
"""

import os
import json
import sys
import argparse
import hashlib
from pathlib import Path

def chunk_file(input_file, output_dir, chunk_size=2000, overlap=200, verbose=False):
    """
    Break down a file into overlapping chunks.
    
    Args:
        input_file (str): Path to the input file
        output_dir (str): Directory to save the chunks
        chunk_size (int): Size of each chunk in characters
        overlap (int): Overlap between chunks in characters
        verbose (bool): Whether to print verbose output
        
    Returns:
        int: Number of chunks created or -1 if error
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Read the file content
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        if verbose:
            print(f"Read {len(content)} characters from {input_file}")
        
        # Calculate file hash for chunk ID prefixes
        file_hash = hashlib.md5(input_file.encode('utf-8')).hexdigest()
        
        # Break the content into chunks
        chunks = []
        position = 0
        chunk_id = 0
        
        while position < len(content):
            # Calculate chunk end position
            end = min(position + chunk_size, len(content))
            
            # Create the chunk
            chunk = {
                "id": f"{file_hash}_{chunk_id}",
                "file": input_file,
                "content": content[position:end],
                "chunk_id": chunk_id
            }
            chunks.append(chunk)
            
            # Move position for next chunk, considering overlap
            position = end - overlap if end < len(content) else end
            chunk_id += 1
        
        # Save chunks to files
        for chunk in chunks:
            output_file = os.path.join(output_dir, f"{chunk['id']}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, indent=2)
                
            if verbose:
                print(f"Saved chunk {chunk['id']} to {output_file}")
        
        if verbose:
            print(f"Created {len(chunks)} chunks with size {chunk_size} and overlap {overlap}")
        
        return len(chunks)
        
    except Exception as e:
        print(f"Error chunking file: {str(e)}")
        return -1

def main():
    """Main function to parse arguments and run the chunker."""
    parser = argparse.ArgumentParser(description='Break down large files into manageable chunks')
    parser.add_argument('--input-file', '-i', type=str, required=True,
                        help='Path to the input file')
    parser.add_argument('--output-dir', '-o', type=str, required=True,
                        help='Directory to save chunks')
    parser.add_argument('--chunk-size', '-c', type=int, default=2000,
                        help='Size of each chunk in characters (default: 2000)')
    parser.add_argument('--overlap', '-l', type=int, default=200,
                        help='Overlap between chunks in characters (default: 200)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Chunk the file
    num_chunks = chunk_file(
        args.input_file, 
        args.output_dir, 
        args.chunk_size, 
        args.overlap, 
        args.verbose
    )
    
    if num_chunks > 0:
        print(f"✓ Successfully created {num_chunks} chunks from {args.input_file}")
        return 0
    else:
        print(f"⚠ Failed to chunk file: {args.input_file}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
